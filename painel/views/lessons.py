from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404,redirect
from core.decorators import painel_required
from courses.models import Lesson
from courses.services import save_lesson_editor,delete_content
from painel.forms import LessonEditorForm
from .common import page

@painel_required
def lesson_edit(request,lesson_id):
    lesson=get_object_or_404(Lesson.objects.select_related('module__course'),pk=lesson_id)
    course=lesson.module.course
    form=LessonEditorForm(request.POST or None,request.FILES or None,instance=lesson,course=course)
    if request.method=='POST':
        if request.POST.get('action')=='delete':
            try:delete_content(lesson,actor=request.user)
            except ValidationError as exc:messages.error(request,' '.join(exc.messages))
            else:return redirect('painel:course_lessons',course_id=course.pk)
        elif form.is_valid():
            item=form.save(commit=False);item.duration_seconds=form.cleaned_data['duration_text']
            try:save_lesson_editor(item,actor=request.user,ebook=form.cleaned_data['ebook'])
            except ValidationError as exc:form.add_error(None,' '.join(exc.messages))
            else:
                messages.success(request,'Aula salva. Alterações de vídeo ou duração reiniciam a posição de retomada.')
                return redirect('painel:lesson_edit',lesson_id=lesson.pk)
    return page(request,'lesson_edit',lesson=lesson,course=course,form=form,materials=lesson.materials.all())
