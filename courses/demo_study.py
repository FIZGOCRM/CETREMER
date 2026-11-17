"""Explicitly synthetic history for the isolated GoMut demonstration account."""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import CommandError
from django.db.models import F
from django.utils import timezone

from .models import Lesson, Progress, StudyDay
from .services import set_lesson_progress


DEMO_COURSES = ('gomut-demo-cardiologia', 'gomut-demo-plantao')
RECENT_MINUTES = (18, 26, 12, 32, 0, 15, 8, 10, 0, 14, 9, 0, 8, 6)
HISTORY_MINUTES = (0, 0, 3, 5, 8, 12, 18, 24, 32, 38, 0)


def prepare_study_history(user):
    if not settings.GOMUT_DEMO_MODE or user.username != 'gomut-demo-student' or user.email != 'aluno@gomut.example':
        raise CommandError('O histórico ilustrativo é exclusivo da conta fictícia na base de demonstração.')
    student = user.student_profile
    today = timezone.localdate()
    created_seconds = 0
    for offset in range(84):
        minutes = RECENT_MINUTES[offset] if offset < len(RECENT_MINUTES) else HISTORY_MINUTES[(offset*7+offset//7*3) % len(HISTORY_MINUTES)]
        if minutes:
            _, created = StudyDay.objects.get_or_create(student=student, date=today-timedelta(days=offset), defaults={'seconds':minutes*60})
            if created:created_seconds += minutes*60
    if not created_seconds:return

    records = Progress.objects.filter(student=student, lesson__module__course__slug__in=DEMO_COURSES)
    completed = list(records.filter(is_completed=True).order_by('pk'))
    if not completed:
        if records.exists():
            raise CommandError('O progresso já foi alterado nessa conta. Preserve-o e conclua uma aula fictícia antes de adicionar o histórico ilustrativo.')
        lesson = Lesson.objects.filter(module__course__slug='gomut-demo-cardiologia',module__course__is_published=True,module__status='published',status='published').order_by('module__order','order','pk').first()
        if not lesson:raise CommandError('Não há aula publicada de demonstração para vincular o tempo ilustrativo.')
        set_lesson_progress(student,lesson,completed=True)
        completed = list(records.filter(is_completed=True))
    # Synthetic replays belong to completed demo lessons. Never change saved
    # positions, completions, assessments or certificates from the user's QA.
    share, extra = divmod(created_seconds,len(completed))
    for index,record in enumerate(completed):
        Progress.objects.filter(pk=record.pk).update(watched_seconds=F('watched_seconds')+share+(index<extra))
