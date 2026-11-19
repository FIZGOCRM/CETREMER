from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect

from core.decorators import painel_required
from courses.models import Course, Lesson, Module
from courses.services import delete_content, save_lesson_editor, save_module
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
    form = LessonEditorForm(
        request.POST if request.method == 'POST' else None, request.FILES or None,
        instance=lesson, course=course,
    )
    if request.method == 'POST':
        if lesson_id and request.POST.get('action') == 'delete':
            try:
                delete_content(lesson, actor=request.user)
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
            else:
                return redirect('painel:course_lessons', course_id=course.pk)
        elif form.is_valid():
            try:
                saved = _save_editor(form, course, request.user, previous_module_id)
            except ValidationError as exc:
                form.add_error(None, ' '.join(exc.messages))
            else:
                messages.success(request, 'Aula salva.')
                return redirect('painel:lesson_edit', lesson_id=saved.pk)
    return page(
        request, 'lesson_edit', lesson=lesson, course=course, form=form,
        editing=bool(lesson_id), materials=lesson.materials.all() if lesson_id else [],
    )
