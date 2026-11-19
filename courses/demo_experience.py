"""Optional course shelves for fictitious QA accounts in prepare_demo."""
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import CommandError
from django.utils import timezone

from users.models import User
from .demo_materials import demo_pdf_bytes
from .models import (
    Course, Enrollment, Lesson, LessonLike, LessonMaterial, LiveEvent, Progress,
    Quiz, SavedLesson, WeeklySelection, WeeklySelectionItem,
)
from .services import create_plan, save_lesson, save_quiz_question


def _qa_user(username, role, password):
    email = username + "@gomut.example"
    user, created = User.objects.get_or_create(username=username, defaults={"role": role, "email": email})
    if (user.role, user.email) != (role, email):
        raise CommandError("O identificador reservado da demonstração pertence a outra conta.")
    if created:
        user.set_password(password)
        user.save(update_fields=["password"])
    return user


def populate_experience(password, owner, original_student):
    reader = _qa_user("aluno-v2", "STUDENT", password)
    if not reader.student_profile.full_name:
        reader.student_profile.full_name = "Marina Souza"
        reader.student_profile.save(update_fields=["full_name"])
    producer = _qa_user("produtor-v2", "CREATOR", password)
    now = timezone.now()
    today = timezone.localdate(now)
    monday = today - timedelta(days=today.weekday())
    course = Course.objects.get(slug="gomut-demo-plantao", creator=owner.creator_profile)
    enrollment, created = Enrollment.objects.get_or_create(student=reader.student_profile, course=course)
    if created:
        create_plan(enrollment, today, actor=producer)
    from django.db.models import Max
    module = course.modules.filter(status="published").order_by("-order", "-pk").first()
    if module and not module.lessons.filter(title="Como usar os materiais · demo v2").exists():
        order = (module.lessons.aggregate(high=Max("order"))["high"] or 0) + 1
        save_lesson(Lesson(module=module, order=order, title="Como usar os materiais · demo v2",
                           description="Conheça as leituras desta mentoria fictícia.",
                           video_url="https://vimeo.com/76979871", duration_seconds=62))
    lessons = list(Lesson.objects.filter(module__course=course, status="published", module__status="published"
                   ).select_related("module").order_by("module__order", "module_id", "order", "pk"))
    if not lessons:
        return
    # Reuse the local demo artwork when available. Empty covers exercise the themed fallback.
    cover = "courses/plantao_cover.png"
    if lessons[0].cover.storage.exists(cover):
        for obj in (lessons[0], lessons[0].module):
            if not obj.cover:
                obj.cover = cover
                obj.save(update_fields=["cover"])
    selection, created = WeeklySelection.objects.get_or_create(course=course, week_start=monday,
                                                               defaults={"created_by": producer})
    if created:
        WeeklySelectionItem.objects.bulk_create([
            WeeklySelectionItem(selection=selection, position=rank, lesson=lesson)
            for rank, lesson in enumerate(lessons[:10], 1)
        ])
    for i, lesson in enumerate(lessons[:3], 1):
        for student in (reader.student_profile, original_student.student_profile):
            position = min(lesson.duration_seconds, i*9)
            activity = now - timedelta(hours=i)
            Progress.objects.get_or_create(student=student, lesson=lesson, defaults={
                "last_position_seconds": position, "max_position_seconds": position,
                "watched_seconds": position, "started_at": activity, "last_heartbeat_at": activity,
            })
            SavedLesson.objects.get_or_create(student=student, lesson=lesson)
        LessonMaterial.objects.get_or_create(lesson=lesson, title=f"Caderno de revisão · exemplo {i}", defaults={
            "file": ContentFile(demo_pdf_bytes(), name=f"caderno-{i}.pdf"), "order": 2})
    LessonLike.objects.get_or_create(student=reader.student_profile, lesson=lessons[0])
    quiz, _ = Quiz.objects.get_or_create(lesson=lessons[0], defaults={"course": course, "kind": "lesson", "is_demo": True})
    question_text = "Onde retomar uma aula já iniciada nesta mentoria?"
    if quiz.is_demo and not quiz.questions.filter(text=question_text).exists():
        order = (quiz.questions.aggregate(high=Max("order"))["high"] or 0) + 1
        save_quiz_question(quiz, order=order, text=question_text, explanation="", actor=producer,
            choices=["Certificados", "Comunidade", "Suporte", "Minha conta", "Continue de onde parou"],
            choice_explanations=["Certificados reúne os documentos emitidos.", "A comunidade reúne discussões.",
                                 "Suporte reúne dúvidas técnicas.", "Minha conta mostra perfil e planos.",
                                 "Essa seção abre a aula na posição salva."], correct_index=4)
    for title, starts, recording in [
        ("Encontro de orientação", now + timedelta(days=1), ""),
        ("Revisão semanal", now + timedelta(days=4), ""),
        ("Orientação gravada", now - timedelta(days=2), "https://vimeo.com/76979871"),
    ]:
        LiveEvent.objects.get_or_create(course=course, title=f"{title} · demo {monday}", defaults={
            "starts_at": starts, "duration_minutes": 45, "recording_url": recording})

