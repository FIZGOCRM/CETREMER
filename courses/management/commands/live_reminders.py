"""Lembrete de aula ao vivo, 1 hora antes (HANDOFF-v2 6.1).

Rodar a cada 15 minutos pelo agendador do servidor:
    python manage.py live_reminders
Pega os encontros que começam entre 60 e 75 minutos a partir de agora e ainda não tiveram lembrete,
avisa os alunos com matrícula ativa e marca `reminder_sent_at` para não repetir.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from courses.models import Enrollment, LiveSession
from users.notify import notify


class Command(BaseCommand):
    help = 'Avisa os alunos 1 hora antes de cada aula ao vivo (rodar a cada 15 minutos).'

    def handle(self, *args, **options):
        now = timezone.now()
        sessions = (LiveSession.objects.select_related('course')
                    .filter(reminder_sent_at__isnull=True, starts_at__gte=now + timedelta(minutes=60),
                            starts_at__lt=now + timedelta(minutes=75)))
        notified = 0
        for session in sessions:
            clock = timezone.localtime(session.starts_at, ZoneInfo('America/Sao_Paulo')).strftime('%H:%M')
            enrollments = (Enrollment.objects.filter(course=session.course, is_active=True)
                           .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).select_related('student__user'))
            for enrollment in enrollments:
                notify(enrollment.student.user, 'live', f'Aula ao vivo hoje às {clock}',
                       f'{session.course.short_name or session.course.title} · {session.title}', reverse('live_classes'))
                notified += 1
            session.reminder_sent_at = now
            session.save(update_fields=['reminder_sent_at'])
        self.stdout.write(f'{notified} aviso(s) enviado(s).')
