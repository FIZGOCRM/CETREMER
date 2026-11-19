"""Populate the local Plantão demo without replacing existing lessons or progress."""
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from courses.demo_materials import demo_pdf_bytes
from courses.models import (
    Category, Course, Enrollment, Lesson, LessonMaterial, LiveEvent, LiveReminder,
    Module, Progress, SavedLesson, WeeklySelection, WeeklySelectionItem,
)
from courses.services import create_plan
from users.models import User


LESSONS = (
    ("Cardiologia", ("ECG em quatro perguntas", "Síncope no pronto atendimento")),
    ("Infectologia", ("Sepse: a primeira hora", "O paciente que piora")),
    ("Via aérea", ("Via aérea sem medo", "Ventilação mecânica descomplicada")),
    ("Ultrassom", ("POCUS à beira-leito", "A janela de ação")),
)
OFFERS = (
    ("PCR sem pânico", "Emergência"),
    ("UTI para plantonistas", "Terapia intensiva"),
    ("Tomografia no plantão", "Imagem e exames"),
    ("Sedação e analgesia", "Via aérea e ventilação"),
    ("Emergências obstétricas", "Emergência"),
)


class Command(BaseCommand):
    help = "Completa a home local criada pelo prepare_demo com aulas, ranking, agenda e vitrine."

    def add_arguments(self, parser):
        parser.add_argument("--student", action="append", help="Conta de aluno da base de demonstração.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.GOMUT_DEMO_MODE:
            raise CommandError("Este comando exige uma base de demonstração com GOMUT_DEMO_MODE.")
        course = Course.objects.filter(slug="gomut-demo-plantao", creator__user__username="gomut-demo-admin").first()
        if not course:
            raise CommandError("Prepare primeiro os dados com prepare_demo --with-course-experience.")
        actor = course.creator.user
        now = timezone.now()
        today = timezone.localdate(now)
        monday = today - timedelta(days=today.weekday())
        video = "https://vimeo.com/76979871"
        lessons = []
        for group, (theme, titles) in enumerate(LESSONS, 3):
            module, _ = Module.objects.get_or_create(course=course, title=theme, defaults={"order": group})
            for order, title in enumerate(titles, 1):
                lesson, _ = Lesson.objects.get_or_create(module=module, title=title, defaults={
                    "order": order, "duration_seconds": 62, "video_url": video,
                    "published_at": now - timedelta(days=group - 2),
                    "description": "Aula ilustrativa com vídeo de demonstração para conhecer o player.",
                })
                lessons.append(lesson)
        cover = "courses/plantao_cover.png"
        if not course.cover_image and course.cover_image.storage.exists(cover):
            course.cover_image = cover
            course.save(update_fields=["cover_image"])
        for lesson in lessons[::2]:
            LessonMaterial.objects.get_or_create(lesson=lesson, title=f"Caderno · {lesson.title}", defaults={
                "file": ContentFile(demo_pdf_bytes(), name=f"caderno-demo-{lesson.pk}.pdf"),
            })
        selection, _ = WeeklySelection.objects.get_or_create(course=course, week_start=monday, defaults={"created_by": actor})
        used = dict(selection.items.values_list("position", "lesson_id"))
        eligible = Lesson.objects.filter(module__course=course, module__status="published",
                                         module__release_month=1, status="published").exclude(pk__in=used.values())
        for position, lesson in zip((i for i in range(1, 11) if i not in used), eligible.order_by("-published_at", "pk")):
            WeeklySelectionItem.objects.create(selection=selection, lesson=lesson, position=position)
        for title, theme in OFFERS:
            category, _ = Category.objects.get_or_create(slug=f"gomut-demo-{slugify(theme)}", defaults={"name": theme})
            Course.objects.get_or_create(slug=f"gomut-demo-vitrine-{slugify(title)}", defaults={
                "creator": course.creator, "title": title, "category": category, "is_published": True,
                "description": "Formação fictícia para visualização da vitrine.",
            })
        event, _ = LiveEvent.objects.get_or_create(course=course, title=f"Discussão de casos · semana de {monday:%d/%m/%Y}",
            defaults={"starts_at": now + timedelta(days=2), "duration_minutes": 60})
        LiveEvent.objects.get_or_create(course=course, title=f"Revisão de ECG · semana de {monday:%d/%m/%Y}",
            defaults={"starts_at": now + timedelta(days=5), "duration_minutes": 45, "kind": "aula_ao_vivo"})
        LiveEvent.objects.get_or_create(course=course, title=f"Plantão comentado · semana de {monday:%d/%m/%Y}",
            defaults={"starts_at": now - timedelta(days=1), "recording_url": video})
        for username in options["student"] or ["aluno-v2"]:
            user = User.objects.filter(username=username, role=User.Role.STUDENT).first()
            if not user:
                raise CommandError(f"Aluno de demonstração não encontrado: {username}")
            student = user.student_profile
            enrollment, created = Enrollment.objects.get_or_create(course=course, student=student)
            if created:
                create_plan(enrollment, today, actor=actor)
            for i, lesson in enumerate(lessons[::2]):
                position = 12 + i * 9
                stamp = now - timedelta(minutes=5 + i)
                Progress.objects.get_or_create(student=student, lesson=lesson, defaults={
                    "started_at": stamp, "last_heartbeat_at": stamp, "last_position_seconds": position,
                    "max_position_seconds": position, "watched_seconds": position,
                })
            for lesson in lessons[1::2]:
                SavedLesson.objects.get_or_create(student=student, lesson=lesson)
            LiveReminder.objects.get_or_create(student=student, event=event)
        self.stdout.write(self.style.SUCCESS(f"Home preparada. {selection.items.count()} destaques na seleção semanal."))
