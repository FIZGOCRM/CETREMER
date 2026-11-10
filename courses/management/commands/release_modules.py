"""Aviso de módulo liberado (HANDOFF-v2 6.1).

Rodar uma vez por dia pelo agendador do servidor:
    python manage.py release_modules
Para cada curso com liberação programada, avisa os alunos de matrícula ativa cujo módulo foi liberado nas
últimas 24 horas. O aviso do sino sempre é criado; o e-mail só sai se o curso tiver
"Avisar o aluno por e-mail quando um módulo for liberado" ligado. Rodar duas vezes no mesmo dia não repete o aviso.
"""
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from courses.models import Enrollment, Module
from users.models import Notification
from users.notify import notify


def released_at(module, enrollment):
    """Momento em que o módulo libera para a matrícula, ou None se não há programação."""
    if module.release_date:
        return timezone.make_aware(datetime.combine(module.release_date, time.min))
    if module.release_after_days is not None:
        return enrollment.enrolled_at + timedelta(days=module.release_after_days)
    return None


class Command(BaseCommand):
    help = 'Avisa os alunos quando um módulo programado é liberado (rodar uma vez por dia).'

    def handle(self, *args, **options):
        now = timezone.now()
        since = now - timedelta(hours=24)
        notified = 0
        modules = (Module.objects.select_related('course')
                   .filter(course__release_mode='scheduled').exclude(course__status='archived')
                   .filter(Q(release_date__isnull=False) | Q(release_after_days__isnull=False)))
        for module in modules:
            course = module.course
            meta = f'{course.short_name or course.title} · {module.title}'
            enrollments = (Enrollment.objects.filter(course=course, is_active=True)
                           .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).select_related('student__user'))
            for enrollment in enrollments:
                moment = released_at(module, enrollment)
                if moment is None or not (since < moment <= now):
                    continue
                user = enrollment.student.user
                if Notification.objects.filter(user=user, kind='module', meta=meta).exists():
                    continue
                notify(user, 'module', 'Novo módulo liberado', meta, reverse('course_home', args=[course.slug]),
                       email=course.notify_module_release)
                notified += 1
        self.stdout.write(f'{notified} aviso(s) enviado(s).')
