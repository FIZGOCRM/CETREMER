from django.core.mail import send_mail
"""Student enrollment use cases without HTTP or email delivery."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils.text import slugify

from courses.models import Course, Enrollment

from .models import User


@transaction.atomic
def enroll_student(*, course, email="", full_name="", student_id=None, source="manual"):
    if source not in {"manual", "import"}:
        raise ValidationError("Origem de matrícula inválida.")
    if student_id:
        user = User.objects.filter(pk=student_id, role=User.Role.STUDENT).first()
        if user is None:
            raise ValidationError("Aluno não encontrado.")
    else:
        email = email.strip().lower()
        validate_email(email)
        user = User.objects.filter(email__iexact=email).first()
        if user and user.role != User.Role.STUDENT:
            raise ValidationError(
                "Este e-mail pertence a outra conta e não pode ser matriculado como aluno."
            )
        if user is None:
            base = slugify(email.split("@")[0])[:130] or "aluno"
            username = base
            suffix = 2
            while User.objects.filter(username=username).exists():
                username = f"{base}{suffix}"
                suffix += 1
            user = User.objects.create_user(
                username=username, email=email, password=None, role=User.Role.STUDENT
            )
    profile = user.student_profile
    if not profile.full_name and full_name:
        profile.full_name = full_name
        profile.full_clean()
        profile.save(update_fields=["full_name"])
    Enrollment.objects.get_or_create(
        student=profile, course=course, defaults={"source": source}
    )
    return user


@dataclass(frozen=True)
class ImportResult:
    created: int
    existing: int
    user_ids: tuple[int, ...]


@transaction.atomic
def import_students(rows, course_ids):
    courses = list(Course.objects.filter(pk__in=course_ids))
    if not courses or len(courses) != len(set(course_ids)):
        raise ValidationError("Seleção de cursos inválida. Leia o arquivo novamente.")
    created = existing = 0
    user_ids = []
    for row in rows:
        if row["status"] not in ("Novo aluno", "Já cadastrado"):
            continue
        was_existing = User.objects.filter(email__iexact=row["email"]).exists()
        for course in courses:
            user = enroll_student(
                course=course,
                email=row["email"],
                full_name=row["name"],
                source="import",
            )
        profile = user.student_profile
        if not profile.cpf and row["cpf"]:
            profile.cpf = row["cpf"]
            profile.save(update_fields=["cpf"])
        existing += int(was_existing)
        created += int(not was_existing)
        user_ids.append(user.pk)
    return ImportResult(created=created, existing=existing, user_ids=tuple(user_ids))

@transaction.atomic
def update_member_account(user, *, email, username=None, avatar=None):
    email=email.strip().lower();validate_email(email)
    if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():raise ValidationError('Este e-mail já está em uso.')
    user.email=email
    if username:user.username=username.strip()
    if avatar:user.avatar=avatar
    user.full_clean();user.save()
    return user

@transaction.atomic
def update_member_personal(user, *, full_name, cpf):
    from courses.services import refresh_certificate_qualification
    profile=user.student_profile
    profile.full_name=full_name.strip()
    if cpf.strip():
        from .validators import validate_cpf
        profile.cpf=validate_cpf(cpf)
    profile.full_clean();profile.save()
    for enrollment in profile.enrollments.all():refresh_certificate_qualification(enrollment)


def update_member_preferences(user, *, new_lessons, live_events):
    profile=user.student_profile
    profile.email_new_lessons=new_lessons;profile.email_live_events=live_events
    profile.save(update_fields=['email_new_lessons','email_live_events'])

@transaction.atomic
def enroll_student_with_plan(*,actor,starts_on,last_day=None,**data):
    from datetime import timedelta
    from courses.services import create_plan
    from django.core.exceptions import PermissionDenied
    if actor.role not in ('ADMIN','CREATOR'):raise PermissionDenied
    user=enroll_student(**data)
    enrollment=Enrollment.objects.get(student=user.student_profile,course=data['course'])
    if enrollment.access_periods.exists():raise ValidationError('Este aluno já tem plano neste curso. Use Gerenciar plano para preservar o histórico.')
    create_plan(enrollment,starts_on,last_day+timedelta(days=1) if last_day else None,actor=actor)
    return user


def send_access_link(user,url):
    """Record the outcome, but never persist a reset token or first-access code."""
    from uuid import uuid4
    from .models import SiteSettings,EmailLog
    site=SiteSettings.load();sent=0;status='not_sent'
    kind='reset_access' if user.has_usable_password() else 'first_access'
    subject=f'Seu acesso à {site.school_name}'
    if site.email_host and user.email and user.is_active:
        try:
            sent=send_mail(subject,f'Olá! Defina sua senha para acessar {site.school_name}: {url}',None,[user.email],fail_silently=False)
            status='sent' if sent else 'failed'
        except Exception:status='failed'
    EmailLog.objects.create(user=user,kind=kind,reference=str(uuid4()),status=status,subject=subject,body='')
    return sent
