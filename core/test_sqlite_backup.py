import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class SQLiteBackupTests(SimpleTestCase):
    def test_backup_validates_weekly_selection_date_constraint(self):
        from django.db.backends.sqlite3._functions import register
        from core.sqlite_backup import backup_database

        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.sqlite3"
            destination = Path(folder) / "backup.sqlite3"
            with closing(sqlite3.connect(source)) as database:
                register(database)
                database.execute("CREATE TABLE selection (week_start DATE NOT NULL "
                                 "CHECK (django_date_extract('week_day', week_start) = 2))")
                database.execute("INSERT INTO selection VALUES ('2026-11-16')")
                database.commit()
            backup_database(source, destination)
            with closing(sqlite3.connect(destination)) as restored:
                self.assertEqual(restored.execute("SELECT week_start FROM selection").fetchone(), ("2026-11-16",))

    def test_backup_preserves_committed_rows_and_checks_integrity(self):
        from core.sqlite_backup import backup_database

        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.sqlite3"
            destination = Path(folder) / "backup.sqlite3"
            with closing(sqlite3.connect(source)) as database:
                database.execute("CREATE TABLE sample (value TEXT)")
                database.execute("INSERT INTO sample VALUES ('preserved')")
                database.commit()
            backup_database(source, destination)
            with closing(sqlite3.connect(destination)) as backup:
                self.assertEqual(
                    backup.execute("SELECT value FROM sample").fetchone()[0],
                    "preserved",
                )
                self.assertEqual(
                    backup.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )

    def test_backup_refuses_overwrite_and_missing_source(self):
        from core.sqlite_backup import backup_database

        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.sqlite3"
            destination = Path(folder) / "backup.sqlite3"
            with self.assertRaises(FileNotFoundError):
                backup_database(source, destination)
            with closing(sqlite3.connect(source)) as database:
                database.execute("CREATE TABLE sample (value TEXT)")
            destination.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                backup_database(source, destination)
            self.assertEqual(destination.read_bytes(), b"keep")
