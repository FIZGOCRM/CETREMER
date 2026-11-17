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
