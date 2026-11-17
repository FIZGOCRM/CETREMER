import sqlite3

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from core.sqlite_backup import backup_database


class Command(BaseCommand):
    help = "Cria um backup SQLite consistente e verifica sua integridade, sem sobrescrever arquivos."

    def add_arguments(self, parser):
        parser.add_argument("destination", help="Caminho de um novo arquivo de backup.")

    def handle(self, *args, **options):
        database = connections["default"]
        if database.vendor != "sqlite":
            raise CommandError("Este comando aceita somente SQLite.")
        try:
            path = backup_database(
                database.settings_dict["NAME"], options["destination"]
            )
        except (OSError, ValueError, sqlite3.Error) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Backup íntegro criado em {path}"))
