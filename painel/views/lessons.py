from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect

from core.decorators import painel_required
from courses.models import Course, Lesson, Module
from courses.services import content_has_history, delete_content, save_lesson_editor, save_module
from painel.forms import LessonEditorForm
from .common import page


@transaction.atomic
def _save_editor(form, course, actor, previous_module_id):
    course = Course.objects.select_for_update().get(pk=course.pk)
    lesson = form.save(commit=False)
    title = form.cleaned_data['new_module_title']
    if title:
        last_order = course.modules.aggregate(last=Max('order'))['last'] or 0
        lesson.module = save_module(Module(course=course, title=title, order=last_order + 1), actor=actor)
    if lesson.module_id != previous_module_id:
        last_order = lesson.module.lessons.aggregate(last=Max('order'))['last'] or 0
        lesson.order = last_order + 1
    lesson.duration_seconds = form.cleaned_data['duration_text']
    return save_lesson_editor(lesson, actor=actor, ebook=form.cleaned_data['ebook'])


@painel_required
def lesson_edit(request, lesson_id=None, course_id=None):
    if lesson_id:
        lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
        course = lesson.module.course
    else:
        course = get_object_or_404(Course, pk=course_id)
        lesson = Lesson(status='draft')
    previous_module_id = lesson.module_id
    action = request.POST.get("action", "")
    if request.method == "POST" and action not in ("", "save_lesson", "delete"):
        return HttpResponseBadRequest("Ação inválida.")
    saving = request.method == "POST" and action != "delete"
    form = LessonEditorForm(
        request.POST if saving else None, request.FILES if saving else None,
        instance=lesson, course=course,
    )
    form.fields['module'].label_from_instance = lambda module: module.title
    module_param = request.GET.get('modulo', '')
    if not lesson_id and module_param.isascii() and module_param.isdecimal() and len(module_param) <= 18:
        selected = form.fields['module'].queryset.filter(pk=module_param).first()
        if selected:
            form.initial['module'] = selected.pk
    if request.method == 'POST':
        if lesson_id and request.POST.get('action') == 'delete':
            try:
                delete_content(lesson, actor=request.user)
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
            else:
                return redirect('painel:course_lessons', course_id=course.pk)
        elif saving and form.is_valid():
            try:
                saved = _save_editor(form, course, request.user, previous_module_id)
            except ValidationError as exc:
                form.add_error(None, ' '.join(exc.messages))
            else:
                messages.success(request, 'Aula salva.' if lesson_id else 'Aula criada.')
                return redirect('painel:lesson_edit', lesson_id=saved.pk)
    return page(
        request, 'lesson_edit', lesson=lesson, course=course, form=form,
        editing=bool(lesson_id), materials=lesson.materials.order_by("order", "pk") if lesson_id else [],
        has_history=content_has_history(lesson) if lesson_id else False,
    )
