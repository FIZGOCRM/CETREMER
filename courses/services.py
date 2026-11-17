"""Course use cases, independent of HTTP requests and templates."""

import secrets

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from users.models import StudentProfile
from users.validators import validate_cpf

from .access import access_decision, has_course_access
from .models import Certificate, Progress
from .selectors import progress_info


def profile_data_ok(profile):
    if not (profile.full_name or "").strip():
        return False
    try:
        validate_cpf(profile.cpf)
    except ValidationError:
        return False
    return True


@transaction.atomic
def set_lesson_progress(student, lesson, *, completed=None):
    """Set completion, or toggle when omitted, updating points atomically.

    SQLite serializes writes; select_for_update is not a lock on SQLite.
    """
    if not has_course_access(student, lesson.module.course):
        raise PermissionDenied("Matrícula necessária.")
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    desired = not progress.is_completed if completed is None else completed
    if desired != progress.is_completed:
        Progress.objects.filter(pk=progress.pk).update(
            is_completed=desired, completed_at=timezone.now()
        )
        if desired:
            StudentProfile.objects.filter(pk=student.pk).update(points=F("points") + 10)
        else:
            # Historical automatic completions did not award points.
            StudentProfile.objects.filter(pk=student.pk, points__gte=10).update(
                points=F("points") - 10
            )
        student.refresh_from_db()
        student.level = student.points // 50 + 1
        student.title = (
            "Grandmaster"
            if student.level >= 5
            else "Scholar"
            if student.level >= 3
            else "Novice"
        )
        student.save(update_fields=["level", "title"])
    info = progress_info(student, lesson.module.course)
    return {
        "status": "success",
        "is_completed": desired,
        "completed_count": info["completed"],
        "total_count": info["total"],
        "percentage": info["pct"],
    }


@transaction.atomic
def issue_enrollment_certificate(enrollment):
    existing = Certificate.objects.filter(enrollment=enrollment).first()
    if existing:
        return existing
    if not access_decision(enrollment).allowed:
        raise ValidationError(
            "Acesso ao curso precisa estar regular para emitir um novo certificado."
        )
    student = enrollment.student
    course = enrollment.course
    if progress_info(student, course)["status"] != "done" or not profile_data_ok(
        student
    ):
        raise ValidationError("Conclua as aulas e informe nome completo e CPF válidos.")
    code = secrets.token_hex(6).upper()
    while Certificate.objects.filter(code=code).exists():
        code = secrets.token_hex(6).upper()
    certificate, _ = Certificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            "code": code,
            "student_name": student.full_name,
            "student_cpf": validate_cpf(student.cpf),
            "course_title": course.title,
            "workload_hours": course.workload_hours,
            "completed_at": timezone.now(),
        },
    )
    return certificate


@transaction.atomic
def save_course(course, *, creator):
    from django.utils.text import slugify

    from .models import Course

    if course.pk is None:
        max_length = Course._meta.get_field("slug").max_length
        base = (slugify(course.title) or "curso")[:max_length].rstrip("-")
        slug = base
        suffix = 2
        while Course.objects.filter(slug=slug).exists():
            ending = f"-{suffix}"
            slug = base[: max_length - len(ending)].rstrip("-") + ending
            suffix += 1
        course.slug = slug
        course.creator = creator
    course.full_clean()
    course.save()
    return course


@transaction.atomic
def save_lesson(lesson, *, materials=()):
    from .models import LessonMaterial

    lesson.full_clean()
    pending = [
        LessonMaterial(lesson=lesson, title=file.name, file=file) for file in materials
    ]
    # Validate every upload before writing the lesson or touching file storage.
    for material in pending:
        material.full_clean(exclude=["lesson"])
    lesson.save()
    for material in pending:
        material.lesson = lesson
        material.save()
    return lesson


@transaction.atomic
def grant_manual_period(*, enrollment, starts_on, paid_through, reference, actor):
    """Append an audited interval; never replace history or invoke billing."""
    from datetime import date, timedelta
    from django.core.exceptions import ValidationError
    from .models import AccessPeriod, Enrollment

    if not (actor.is_staff or actor.role in ("ADMIN", "CREATOR")):
        raise PermissionDenied("Acesso exclusivo da administração.")
    if paid_through < starts_on or paid_through == date.max:
        raise ValidationError("Período inválido.")
    locked = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    ends_on = paid_through + timedelta(days=1)
    reference = "manual:" + str(reference)
    existing = locked.access_periods.filter(source=AccessPeriod.Source.MANUAL, reference=reference).first()
    if existing:
        if existing.starts_on != starts_on or existing.ends_on != ends_on:
            raise ValidationError("Esta confirmação já foi usada para outro período. Recarregue e revise.")
        return existing
    if locked.access_periods.filter(starts_on__lt=ends_on, ends_on__gt=starts_on).exists():
        raise ValidationError("O período coincide com um acesso já registrado. O histórico foi preservado.")
    period = AccessPeriod(enrollment=locked, starts_on=starts_on, ends_on=ends_on,
                          grace_days=3, source=AccessPeriod.Source.MANUAL,
                          reference=reference, created_by=actor)
    period.full_clean()
    period.save()
    locked.access_policy = Enrollment.AccessPolicy.PERIODS
    locked.save(update_fields=["access_policy"])
    return period

# Planos V1: um período corrente, com alterações auditadas.
def add_calendar_months(value, months):
    from calendar import monthrange
    from datetime import date
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(value.day, monthrange(year, month + 1)[1]))


def _plan_actor(actor):
    if not actor or not actor.is_active or actor.role not in ('ADMIN', 'CREATOR'):
        raise PermissionDenied('Acesso exclusivo da administração.')


def _current_period(enrollment):
    periods = list(enrollment.access_periods.select_for_update())
    if len(periods) != 1:
        raise ValidationError('A matrícula precisa ter exatamente um período. Revise o histórico antes de continuar.')
    return periods[0]


def _record_plan(enrollment, period, action, actor, old=None, reason_code='', reason_text=''):
    from .models import AccessChange
    AccessChange.objects.create(enrollment=enrollment, action=action,
        old_starts_on=old[0] if old else None, old_ends_on=old[1] if old else None,
        new_starts_on=period.starts_on, new_ends_on=period.ends_on,
        actor=actor, reason_code=reason_code, reason_text=reason_text)


def _contract_end(enrollment, period):
    change = enrollment.access_changes.filter(action__in=['created', 'corrected']).last()
    return change.new_ends_on if change else period.ends_on


@transaction.atomic
def create_plan(enrollment, starts_on, ends_on=None, *, actor):
    from .models import AccessPeriod, Enrollment
    _plan_actor(actor)
    enrollment = Enrollment.objects.select_for_update().select_related('course').get(pk=enrollment.pk)
    if enrollment.access_periods.exists():
        raise ValidationError('Já existe um plano. Use Corrigir datas; o histórico deve ser preservado.')
    ends_on = ends_on or add_calendar_months(starts_on, enrollment.course.plan_months)
    period = AccessPeriod(enrollment=enrollment, starts_on=starts_on, ends_on=ends_on,
        grace_days=3, source='manual', reference='v1-plan', created_by=actor)
    period.full_clean(); period.save()
    enrollment.plan_started_on = starts_on
    enrollment.access_policy = 'periods'
    enrollment.save(update_fields=['plan_started_on', 'access_policy'])
    _record_plan(enrollment, period, 'created', actor)
    return period


def _prepare_plan_change(enrollment, actor):
    from .models import Enrollment
    _plan_actor(actor)
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    period = _current_period(enrollment)
    if not enrollment.access_changes.exists():
        _record_plan(enrollment, period, 'created', actor, reason_text='Registro do período histórico existente, sem alterar datas.')
    return enrollment, period


@transaction.atomic
def end_plan_early(enrollment, end_date, reason, *, actor, reason_text=''):
    enrollment, period = _prepare_plan_change(enrollment, actor)
    if reason not in ('withdrawal', 'nonpayment', 'student_request', 'other'):
        raise ValidationError('Escolha um motivo de encerramento.')
    if reason == 'other' and not reason_text.strip():
        raise ValidationError('Explique o motivo do encerramento.')
    if end_date > _contract_end(enrollment, period):
        raise ValidationError('O encerramento não pode ultrapassar o fim contratual.')
    old = (period.starts_on, period.ends_on)
    period.ends_on = end_date
    period.grace_days = 0
    period.ended_early = True
    period.full_clean(); period.save(update_fields=['ends_on', 'grace_days', 'ended_early'])
    _record_plan(enrollment, period, 'ended_early', actor, old, reason, reason_text.strip())
    return period


@transaction.atomic
def reactivate_plan(enrollment, until_date, *, actor):
    enrollment, period = _prepare_plan_change(enrollment, actor)
    last = enrollment.access_changes.last()
    if not period.ended_early:
        raise ValidationError('Só é possível reativar um plano encerrado antecipadamente.')
    contract_end = _contract_end(enrollment, period)
    if until_date > contract_end or until_date <= timezone.localdate():
        raise ValidationError('A reativação deve terminar no futuro, até o fim contratual corrigido.')
    old = (period.starts_on, period.ends_on)
    period.ends_on = until_date
    period.grace_days = 3 if until_date == contract_end else 0
    period.ended_early = False
    period.full_clean(); period.save(update_fields=['ends_on', 'grace_days', 'ended_early'])
    _record_plan(enrollment, period, 'reactivated', actor, old)
    return period


@transaction.atomic
def correct_plan_dates(enrollment, new_start, new_end, reason, *, actor):
    if not reason.strip():
        raise ValidationError('Informe o motivo da correção.')
    enrollment, period = _prepare_plan_change(enrollment, actor)
    old = (period.starts_on, period.ends_on)
    was_early = period.ended_early
    period.starts_on, period.ends_on = new_start, new_end
    period.grace_days = 0 if was_early else 3
    period.full_clean(); period.save(update_fields=['starts_on', 'ends_on', 'grace_days'])
    enrollment.plan_started_on = new_start
    enrollment.access_policy = 'periods'
    enrollment.save(update_fields=['plan_started_on', 'access_policy'])
    _record_plan(enrollment, period, 'corrected', actor, old, reason_text=reason.strip())
    return period


def plan_status(enrollment, *, on=None):
    from datetime import timedelta
    on = on or timezone.localdate()
    periods = list(enrollment.access_periods.all())
    if not periods:
        return {'state': 'active' if enrollment.access_policy == 'unrestricted' else 'pending', 'label': 'Sem plano definido'}
    period = max(periods, key=lambda p: p.ends_on)
    decision = access_decision(enrollment, on=on)
    last = enrollment.access_changes.last()
    early = period.ended_early
    days = (period.ends_on-on).days
    state = 'ended'
    if decision.state == 'grace':
        state = 'grace'; days = (period.ends_on+timedelta(days=period.grace_days)-on).days
    elif decision.allowed:
        state = 'ending_soon' if not early and 0 < days <= 30 else 'active'
    elif decision.state == 'pending':
        state = 'pending'
    labels = {'active': 'Ativo', 'ending_soon': f'Termina em {days} dias', 'grace': f'Seu acesso termina em {days} dias', 'ended': 'Encerrado', 'pending': 'Aguardando início'}
    month = 1
    if enrollment.plan_started_on:
        month = max(1, (on.year-enrollment.plan_started_on.year)*12+on.month-enrollment.plan_started_on.month+1)
        if on < add_calendar_months(enrollment.plan_started_on, month-1):
            month = max(1, month-1)
    milestone = 'grace' if state == 'grace' else str(next((n for n in (7,15,30) if 0 < days <= n), '')) if state == 'ending_soon' else ''
    reason_labels = {'withdrawal': 'Desistência', 'nonpayment': 'Inadimplência', 'student_request': 'Pedido do aluno', 'other': 'Outro'}
    reason = (last.reason_text or reason_labels.get(last.reason_code, 'Encerramento antecipado')) if early else 'Fim do período'
    return {'state': state, 'label': labels[state], 'days': days, 'starts_on': period.starts_on,
        'ends_on': period.ends_on, 'last_day': period.ends_on-timedelta(days=1), 'month': month,
        'reason': reason,
        'milestone': milestone, 'period': period}
