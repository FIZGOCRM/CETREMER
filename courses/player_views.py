import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.http import json_error
from .access import access_decision
from .forms import HeartbeatForm
from .models import Enrollment, Lesson
from .services import finish_video, record_heartbeat


@login_required
@require_POST
def heartbeat(request, lesson_id):
    return _respond(request, lesson_id)


@login_required
@require_POST
def ended(request, lesson_id):
    return _respond(request, lesson_id, ended=True)


def _respond(request, lesson_id, *, ended=False):
    if request.user.role != 'STUDENT':
        return json_error('Acesso exclusivo do aluno.', status=403, code='student_required')
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    student = request.user.student_profile
    try:
        if ended:
            result = finish_video(student, lesson)
        else:
            try:
                data = json.loads(request.body if request.content_type == 'application/json' else request.POST.get('payload', ''))
            except (ValueError, UnicodeDecodeError):
                return json_error('Envie os dados do vídeo em JSON válido.', status=400, code='invalid_json')
            if not isinstance(data, dict):
                return json_error('Dados do vídeo inválidos.', status=400, code='invalid_input')
            form = HeartbeatForm(data)
            if not form.is_valid():
                return json_error('Posição ou estado do vídeo inválido.', status=400, code='invalid_input')
            result = record_heartbeat(student, lesson, **form.cleaned_data)
    except PermissionDenied as exc:
        enrollment = Enrollment.objects.filter(student=student, course=lesson.module.course).first()
        is_ended = enrollment is not None and not access_decision(enrollment).allowed
        return JsonResponse({'access': 'ended' if is_ended else 'denied', 'message': str(exc),
            'url': reverse('lesson_detail', args=[lesson.module.course.slug, lesson.pk])}, status=403)
    except ValidationError as exc:
        return json_error(' '.join(exc.messages), status=400, code='invalid_input')
    return JsonResponse(result)


@login_required
@require_POST
def lesson_reaction(request, lesson_id, kind):
    from .engagement_services import set_lesson_reaction

    if request.user.role != "STUDENT":
        return json_error("Acesso exclusivo do aluno.", status=403, code="student_required")
    if kind not in ("like", "saved"):
        return json_error("Ação desconhecida.", status=404, code="unknown_action")
    lesson = get_object_or_404(Lesson.objects.select_related("module__course"), pk=lesson_id)
    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        active = data.get("active") if isinstance(data, dict) else None
        if active not in ("true", "false") and type(active) is not bool:
            raise ValueError
    except (UnicodeDecodeError, ValueError):
        return json_error("Informe um estado válido.", status=400, code="invalid_input")
    try:
        result = set_lesson_reaction(request.user.student_profile, lesson, kind, active in (True, "true"))
    except PermissionDenied as exc:
        return json_error(str(exc), status=403, code="access_denied")
    return JsonResponse({"active": result})
