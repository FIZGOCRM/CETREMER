import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from core.http import json_error
from .access import require_lesson_access
from .forms import QuizAnswerForm
from .models import Quiz, QuizAttempt, Course, Enrollment
from .selectors import public_quiz_attempt, quiz_attempt_result
from .services import start_quiz, answer_quiz, finish_quiz, submit_final_quiz
from .access import access_decision
from django.shortcuts import render
from .selectors import active_final_quiz, progress_info


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
        if not attempt.quiz.course.is_published or not attempt.quiz.is_active:
            raise PermissionDenied('Este quiz foi desativado.')
        if attempt.quiz.kind == 'final':
            enrollment = Enrollment.objects.filter(student=student, course=attempt.quiz.course).first()
            if not access_decision(enrollment).allowed:
                raise PermissionDenied('Plano encerrado.')
        else:
            require_lesson_access(student, attempt.quiz.lesson)
        result = quiz_attempt_result(attempt)
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(result)


@login_required
@require_POST
def submit_final(request, attempt_id):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return _error(exc)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=student)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        result = submit_final_quiz(student, attempt, data.get('answers'))
    except (ValueError, UnicodeDecodeError):
        return json_error('Envie todas as respostas em JSON válido.', status=400, code='invalid_input')
    except (PermissionDenied, ValidationError) as exc:
        return _error(exc)
    return JsonResponse(result)


@login_required
@require_GET
def final_assessment(request, course_slug):
    try:
        student = _student(request)
    except PermissionDenied as exc:
        return _error(exc)
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    enrollment = get_object_or_404(Enrollment.objects.prefetch_related('access_periods'), student=student, course=course)
    decision = access_decision(enrollment)
    if not decision.allowed:
        from .services import plan_status
        return render(request, 'courses/access_pending.html', {'course':course, 'access':decision, 'plan':plan_status(enrollment)}, status=403)
    quiz = active_final_quiz(course)
    if quiz is None:
        from django.http import Http404
        raise Http404
    info = progress_info(student, course)
    latest = quiz.attempts.filter(student=student, finished_at__isnull=False).order_by('-finished_at','-id').first()
    return render(request, 'courses/final_assessment.html', {'course':course, 'quiz':quiz, 'item':info,
        'ready': bool(info['total'] and info['completed'] == info['total']), 'quiz_result':quiz_attempt_result(latest) if latest else None})
