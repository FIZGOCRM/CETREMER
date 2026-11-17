import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from core.http import json_error
from .access import require_lesson_access
from .forms import QuizAnswerForm
from .models import Quiz, QuizAttempt
from .selectors import public_quiz_attempt, quiz_attempt_result
from .services import start_quiz, answer_quiz, finish_quiz


def _student(request):
    if request.user.role != 'STUDENT':
        raise PermissionDenied('Acesso exclusivo do aluno.')
    return request.user.student_profile


def _error(exc):
    if isinstance(exc, PermissionDenied):
        return json_error(str(exc), status=403, code='quiz_unavailable')
    return json_error(' '.join(exc.messages), status=400, code='invalid_input')


@login_required
@require_POST
def start(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related('lesson__module__course'), pk=quiz_id)
    try:
        attempt = start_quiz(_student(request), quiz)
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(public_quiz_attempt(attempt), status=201)


@login_required
@require_POST
def answer(request, attempt_id):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return _error(exc)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=student)
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return json_error('Envie a resposta em JSON válido.', status=400, code='invalid_json')
    if not isinstance(data, dict):
        return json_error('Resposta inválida.', status=400, code='invalid_input')
    form = QuizAnswerForm(data)
    if not form.is_valid():
        return json_error('Escolha uma alternativa válida.', status=400, code='invalid_input')
    try:
        result = answer_quiz(student, attempt, **form.cleaned_data)
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(result)


@login_required
@require_POST
def finish(request, attempt_id):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return _error(exc)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=student)
    try:
        result = finish_quiz(student, attempt)
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(result)


@login_required
@require_GET
def result(request, attempt_id):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return _error(exc)
    attempt = get_object_or_404(QuizAttempt.objects.select_related('quiz__lesson__module__course'), pk=attempt_id, student=student)
    try:
        if not attempt.quiz.is_active:
            raise PermissionDenied('Este quiz foi desativado.')
        require_lesson_access(student, attempt.quiz.lesson)
        result = quiz_attempt_result(attempt)
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(result)
