"""Consistent SQLite snapshots using the online backup API, including WAL data."""

import sqlite3
from contextlib import closing
from pathlib import Path


def backup_database(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_file():
        raise FileNotFoundError("O banco SQLite de origem não existe.")
    # Exclusive creation also prevents accidentally replacing the live database.
    with destination.open("xb"):
        pass
    try:
        with closing(
            sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        ) as database:
            with closing(sqlite3.connect(destination)) as snapshot:
                database.backup(snapshot)
                if snapshot.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError("A verificação de integridade do backup falhou.")
    except Exception:
        # Only remove the incomplete file exclusively created by this operation.
        destination.unlink(missing_ok=True)
        raise
    return destination
