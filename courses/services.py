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
