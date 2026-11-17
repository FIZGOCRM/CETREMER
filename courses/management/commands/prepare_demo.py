"""Opt-in, non-destructive fixture for the local member demonstration."""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from courses.models import AccessPeriod, Category, Course, Enrollment, Lesson, Module
from users.models import User


class Command(BaseCommand):
    help = "Cria dois cursos e acessos fictícios; exige GOMUT_DEMO_MODE=True. Não apaga dados."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Senha apenas para novas contas de demonstração.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.GOMUT_DEMO_MODE:
            raise CommandError("Prepare uma base de demonstração separada e habilite GOMUT_DEMO_MODE.")
        password = options["password"]
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        admin, created = User.objects.get_or_create(username="gomut-demo-admin", defaults={
            "email": "admin@gomut.example", "role": User.Role.CREATOR, "is_staff": True,
        })
        if created:
            admin.set_password(password)
            admin.save(update_fields=["password"])
        if not hasattr(admin, "creator_profile"):
            raise CommandError("O identificador de demonstração já pertence a outro perfil.")
        student, created = User.objects.get_or_create(username="gomut-demo-student", defaults={
            "email": "aluno@gomut.example", "role": User.Role.STUDENT,
        })
        if created:
            student.set_password(password)
            student.save(update_fields=["password"])
            student.student_profile.full_name = "Marina Souza · Demonstração"
            student.student_profile.save()
        if student.role != User.Role.STUDENT:
            raise CommandError("O identificador de demonstração já pertence a outro perfil.")
        category, _ = Category.objects.get_or_create(slug="gomut-demo-emergencia", defaults={"name": "Emergência", "color": "teal"})
        courses = [
            ("plantao", "Plantão sem GPT", "Raciocínio clínico passo a passo e organização do atendimento em emergência."),
            ("cardiologia", "Emergências cardiovasculares", "Fundamentos de avaliação, ECG e discussão de situações clínicas. Conteúdo fictício para demonstração."),
        ]
        today = timezone.localdate()
        for slug, title, description in courses:
            course, _ = Course.objects.get_or_create(slug="gomut-demo-"+slug, defaults={
                "title": title, "description": description, "creator": admin.creator_profile,
                "category": category, "is_published": True,
            })
            for n, module_title in enumerate(["Fundamentos", "Discussão de casos"], 1):
                module, _ = Module.objects.get_or_create(course=course, order=n, defaults={"title": module_title})
                for order, lesson_title in enumerate(["Introdução ao atendimento", "Aplicação prática"], 1):
                    Lesson.objects.get_or_create(module=module, order=order, defaults={
                        "title": lesson_title, "description": "Aula fictícia. O player utiliza um vídeo público de demonstração do Vimeo, sem conteúdo clínico deste curso.",
                        "video_url": "https://vimeo.com/76979871", "duration_seconds": 62,
                    })
            enrollment, _ = Enrollment.objects.get_or_create(student=student.student_profile, course=course,
                defaults={"access_policy": Enrollment.AccessPolicy.PERIODS})
            AccessPeriod.objects.get_or_create(enrollment=enrollment, source="manual", reference="gomut-demo-initial", defaults={
                "starts_on": today, "ends_on": today+timedelta(days=30), "grace_days": 3, "created_by": admin,
            })
        self.stdout.write(self.style.SUCCESS("Demonstração preparada: dois cursos; aluno@gomut.example e admin@gomut.example. Senhas existentes foram preservadas."))
