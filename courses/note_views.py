from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods, require_POST

from core.http import json_error
from .access import require_lesson_access
from .forms import LessonNoteForm
from .models import Lesson, LessonNote
from .services import create_lesson_note, delete_lesson_note


def _student(request):
    if request.user.role != 'STUDENT':
        raise PermissionDenied('Acesso exclusivo do aluno.')
    return request.user.student_profile


def _note_data(note):
    return {'id': note.pk, 'position_seconds': note.position_seconds, 'text': note.text, 'created_at': note.created_at.isoformat()}


@login_required
@require_http_methods(['GET', 'POST'])
def notes(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    try:
        student = _student(request)
        require_lesson_access(student, lesson)
    except PermissionDenied as exc:
        return json_error(str(exc), status=403, code='content_unavailable')
    if request.method == 'GET':
        return JsonResponse({'notes': [_note_data(note) for note in lesson.notes.filter(student=student)]})
    form = LessonNoteForm(request.POST)
    if not form.is_valid():
        return json_error('Escreva a anotação e informe um minuto válido.', status=400, code='invalid_input')
    try:
        note = create_lesson_note(student, lesson, **form.cleaned_data)
    except ValidationError as exc:
        return json_error(' '.join(exc.messages), status=400, code='invalid_input')
    if 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse(_note_data(note), status=201)
    return redirect('lesson_detail', course_slug=lesson.module.course.slug, lesson_id=lesson.pk)


@login_required
@require_POST
def delete_note(request, lesson_id, note_id):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return json_error(str(exc), status=403, code='student_required')
    note = get_object_or_404(LessonNote.objects.select_related('lesson__module__course'), pk=note_id, lesson_id=lesson_id, student=student)
    lesson = note.lesson
    try:
        delete_lesson_note(student, note)
    except PermissionDenied as exc:
        return json_error(str(exc), status=403, code='content_unavailable')
    if 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'deleted': True})
    return redirect('lesson_detail', course_slug=lesson.module.course.slug, lesson_id=lesson.pk)
