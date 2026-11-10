"""Apaga de vez as aulas excluídas com Desfazer há mais de 7 dias (HANDOFF-v2 6.1).

Rodar uma vez por dia pelo agendador do servidor:
    python manage.py purge_deleted
    python manage.py purge_deleted --days 14      (outro prazo)
    python manage.py purge_deleted --dry-run      (só mostra quantas seriam apagadas)
O progresso dos alunos e os materiais dessas aulas saem junto (cascata do banco).
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from courses.models import Lesson


class Command(BaseCommand):
    help = 'Apaga de vez as aulas excluídas há mais de 7 dias.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        limit = timezone.now() - timedelta(days=options['days'])
        old = Lesson.all_objects.filter(deleted_at__isnull=False, deleted_at__lt=limit)
        total = old.count()
        if options['dry_run']:
            self.stdout.write(f'{total} aula(s) seriam apagadas.')
            return
        old.delete()
        self.stdout.write(f'{total} aula(s) apagadas de vez.')
