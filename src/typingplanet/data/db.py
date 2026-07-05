"""SQLite connection management."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .migrations import Migrator


def connect(path: Optional[Path | str] = None) -> sqlite3.Connection:
    """Open (and migrate) the database at ``path``.

    Passing ``None`` uses the default user data location.
    """
    if path is None:
        from ..config.paths import db_path

        path = db_path()
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.OperationalError:
        # WAL is unsupported on some network filesystems; fall back silently.
        pass
    Migrator(conn).run()
    return conn
