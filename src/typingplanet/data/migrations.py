"""Versioned schema migrations.

Migrations are append-only and tracked in the ``schema_meta`` table. Adding a
new migration is a matter of appending a ``Migration`` to ``MIGRATIONS``; the
runner applies only those with a version higher than the recorded one.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Callable

MigrationFn = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migration:
    version: int
    description: str
    apply: MigrationFn


_V1 = """
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    avatar TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons_progress (
    profile_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    best_wpm REAL NOT NULL DEFAULT 0,
    best_accuracy REAL NOT NULL DEFAULT 0,
    best_stars INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_played_at TEXT,
    unlocked INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (profile_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    wpm REAL NOT NULL,
    accuracy REAL NOT NULL,
    correct_chars INTEGER NOT NULL,
    error_chars INTEGER NOT NULL,
    duration_s REAL NOT NULL,
    stars INTEGER NOT NULL,
    completed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_profile
    ON attempts(profile_id, completed_at DESC);

CREATE TABLE IF NOT EXISTS achievements (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT 'star'
);

CREATE TABLE IF NOT EXISTS unlocked_achievements (
    achievement_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    unlocked_at TEXT NOT NULL,
    PRIMARY KEY (achievement_id, profile_id)
);
"""


def _apply_v1(conn: sqlite3.Connection) -> None:
    conn.executescript(_V1)


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "initial schema", _apply_v1),
)


class Migrator:
    """Applies pending migrations to a connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _ensure_meta(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_meta ("
            "key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )

    def _current_version(self) -> int:
        row = self.conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        return int(row[0]) if row else 0

    def _set_version(self, version: int) -> None:
        self.conn.execute(
            "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(version),),
        )

    def run(self, migrations: tuple[Migration, ...] = MIGRATIONS) -> int:
        self._ensure_meta()
        current = self._current_version()
        for m in migrations:
            if m.version > current:
                m.apply(self.conn)
                self._set_version(m.version)
                current = m.version
        self.conn.commit()
        return current
