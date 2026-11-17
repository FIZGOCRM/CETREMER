from collections import Counter
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from courses.quiz_importing import parse_quiz_csv, quiz_import_targets
from courses.services import import_quiz_rows


class Command(BaseCommand):
    help = 'Importa perguntas UTF-8 por curso/aula; --dry-run valida sem gravar.'

    def add_arguments(self, parser):
        parser.add_argument('arquivo')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        try:
            rows, errors = parse_quiz_csv(Path(options['arquivo']))
        except (OSError, ValueError, UnicodeDecodeError, csv.Error) as exc:
            raise CommandError(f'Arquivo inválido: {exc}') from exc
        for (course, lesson), count in Counter((row.course.slug, row.lesson.title if row.lesson else 'Avaliação final') for row in rows).items():
            self.stdout.write(f'{course} / {lesson}: {count} pergunta(s).')
        _, unlisted, conflicts = quiz_import_targets(rows)
        errors.extend(conflicts)
        for quiz in unlisted:
            self.stdout.write(f'{quiz.course.slug} / {quiz.lesson.title}: fora do CSV; quiz será desativado, preservando histórico.')
        if errors:
            for error in errors:
                self.stdout.write(error)
            raise CommandError('Arquivo recusado; nenhuma pergunta foi gravada. '+ ' | '.join(errors))
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Prévia válida. Nenhuma alteração foi gravada.'))
            return
        try:
            import_quiz_rows(rows)
        except ValidationError as exc:
            raise CommandError(' '.join(exc.messages)) from exc
        self.stdout.write(self.style.SUCCESS(f'{len(rows)} pergunta(s) importada(s) em uma transação.'))
