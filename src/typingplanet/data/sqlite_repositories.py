"""SQLite implementations of the repository contracts.

``DataStore`` is the single entry point: it opens/migrates the database and
exposes the four repositories. The rest of the app only sees the Protocol
types, so this module can be replaced without touching business logic.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from ..domain.models import (
    Achievement,
    AttemptResult,
    Difficulty,
    LessonProgress,
    Profile,
    UnlockedAchievement,
    new_id,
    utcnow,
)
from .db import connect


def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _str_to_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


class SqliteProfileRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, name: str, avatar: str = "default") -> Profile:
        profile = Profile(name=name, avatar=avatar)
        self.conn.execute(
            "INSERT INTO profiles(id, name, avatar, created_at) VALUES(?, ?, ?, ?)",
            (profile.id, profile.name, profile.avatar, _dt_to_str(profile.created_at)),
        )
        self.conn.commit()
        return profile

    def get(self, profile_id: str) -> Optional[Profile]:
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        return _row_to_profile(row) if row else None

    def list_all(self) -> Sequence[Profile]:
        rows = self.conn.execute(
            "SELECT * FROM profiles ORDER BY created_at ASC"
        ).fetchall()
        return [_row_to_profile(r) for r in rows]

    def update(self, profile: Profile) -> Profile:
        self.conn.execute(
            "UPDATE profiles SET name = ?, avatar = ? WHERE id = ?",
            (profile.name, profile.avatar, profile.id),
        )
        self.conn.commit()
        return profile

    def delete(self, profile_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        self.conn.commit()
        # cascade-clean child rows
        for table in ("attempts", "lessons_progress", "unlocked_achievements"):
            self.conn.execute(f"DELETE FROM {table} WHERE profile_id = ?", (profile_id,))
        self.conn.commit()
        return cur.rowcount > 0


class SqliteAttemptRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add(self, result: AttemptResult) -> AttemptResult:
        self.conn.execute(
            "INSERT INTO attempts(id, profile_id, lesson_id, wpm, accuracy, "
            "correct_chars, error_chars, duration_s, stars, completed_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                result.id,
                result.profile_id,
                result.lesson_id,
                result.wpm,
                result.accuracy,
                result.correct_chars,
                result.error_chars,
                result.duration_s,
                result.stars,
                _dt_to_str(result.completed_at),
            ),
        )
        self.conn.commit()
        return result

    def list_by_profile(self, profile_id: str, limit: int = 50) -> Sequence[AttemptResult]:
        rows = self.conn.execute(
            "SELECT * FROM attempts WHERE profile_id = ? "
            "ORDER BY completed_at DESC LIMIT ?",
            (profile_id, limit),
        ).fetchall()
        return [_row_to_attempt(r) for r in rows]

    def best_for_lesson(self, profile_id: str, lesson_id: str) -> Optional[AttemptResult]:
        row = self.conn.execute(
            "SELECT * FROM attempts WHERE profile_id = ? AND lesson_id = ? "
            "ORDER BY stars DESC, wpm DESC LIMIT 1",
            (profile_id, lesson_id),
        ).fetchone()
        return _row_to_attempt(row) if row else None

    def count_for_lesson(self, profile_id: str, lesson_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM attempts WHERE profile_id = ? AND lesson_id = ?",
            (profile_id, lesson_id),
        ).fetchone()
        return int(row["c"])


class SqliteProgressRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, profile_id: str, lesson_id: str) -> Optional[LessonProgress]:
        row = self.conn.execute(
            "SELECT * FROM lessons_progress WHERE profile_id = ? AND lesson_id = ?",
            (profile_id, lesson_id),
        ).fetchone()
        return _row_to_progress(row) if row else None

    def upsert(self, progress: LessonProgress) -> LessonProgress:
        self.conn.execute(
            "INSERT INTO lessons_progress(profile_id, lesson_id, best_wpm, "
            "best_accuracy, best_stars, attempts, last_played_at, unlocked) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(profile_id, lesson_id) DO UPDATE SET "
            "best_wpm = excluded.best_wpm, best_accuracy = excluded.best_accuracy, "
            "best_stars = excluded.best_stars, attempts = excluded.attempts, "
            "last_played_at = excluded.last_played_at, unlocked = excluded.unlocked",
            (
                progress.profile_id,
                progress.lesson_id,
                progress.best_wpm,
                progress.best_accuracy,
                progress.best_stars,
                progress.attempts,
                _dt_to_str(progress.last_played_at),
                1 if progress.unlocked else 0,
            ),
        )
        self.conn.commit()
        return progress

    def list_for_profile(self, profile_id: str) -> Sequence[LessonProgress]:
        rows = self.conn.execute(
            "SELECT * FROM lessons_progress WHERE profile_id = ?", (profile_id,)
        ).fetchall()
        return [_row_to_progress(r) for r in rows]

    def list_unlocked_lessons(self, profile_id: str) -> Sequence[str]:
        rows = self.conn.execute(
            "SELECT lesson_id FROM lessons_progress WHERE profile_id = ? AND unlocked = 1",
            (profile_id,),
        ).fetchall()
        return [r["lesson_id"] for r in rows]


class SqliteAchievementRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_definitions(self) -> Sequence[Achievement]:
        rows = self.conn.execute("SELECT * FROM achievements ORDER BY id").fetchall()
        return [_row_to_achievement(r) for r in rows]

    def register_definition(self, achievement: Achievement) -> None:
        self.conn.execute(
            "INSERT INTO achievements(id, name, description, icon) VALUES(?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name = excluded.name, "
            "description = excluded.description, icon = excluded.icon",
            (achievement.id, achievement.name, achievement.description, achievement.icon),
        )
        self.conn.commit()

    def unlock(self, profile_id: str, achievement_id: str) -> Optional[UnlockedAchievement]:
        existing = self.is_unlocked(profile_id, achievement_id)
        if existing:
            return None
        ua = UnlockedAchievement(achievement_id=achievement_id, profile_id=profile_id)
        self.conn.execute(
            "INSERT INTO unlocked_achievements(achievement_id, profile_id, unlocked_at) "
            "VALUES(?, ?, ?)",
            (achievement_id, profile_id, _dt_to_str(ua.unlocked_at)),
        )
        self.conn.commit()
        return ua

    def list_unlocked(self, profile_id: str) -> Sequence[UnlockedAchievement]:
        rows = self.conn.execute(
            "SELECT * FROM unlocked_achievements WHERE profile_id = ? "
            "ORDER BY unlocked_at DESC",
            (profile_id,),
        ).fetchall()
        return [_row_to_unlocked(r) for r in rows]

    def is_unlocked(self, profile_id: str, achievement_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM unlocked_achievements "
            "WHERE profile_id = ? AND achievement_id = ?",
            (profile_id, achievement_id),
        ).fetchone()
        return row is not None


# ---- row mappers -----------------------------------------------------------


def _row_to_profile(row: sqlite3.Row) -> Profile:
    return Profile(
        id=row["id"],
        name=row["name"],
        avatar=row["avatar"],
        created_at=_str_to_dt(row["created_at"]) or utcnow(),
    )


def _row_to_attempt(row: sqlite3.Row) -> AttemptResult:
    return AttemptResult(
        id=row["id"],
        profile_id=row["profile_id"],
        lesson_id=row["lesson_id"],
        wpm=row["wpm"],
        accuracy=row["accuracy"],
        correct_chars=row["correct_chars"],
        error_chars=row["error_chars"],
        duration_s=row["duration_s"],
        stars=row["stars"],
        completed_at=_str_to_dt(row["completed_at"]) or utcnow(),
    )


def _row_to_progress(row: sqlite3.Row) -> LessonProgress:
    return LessonProgress(
        profile_id=row["profile_id"],
        lesson_id=row["lesson_id"],
        best_wpm=row["best_wpm"],
        best_accuracy=row["best_accuracy"],
        best_stars=row["best_stars"],
        attempts=row["attempts"],
        last_played_at=_str_to_dt(row["last_played_at"]),
        unlocked=bool(row["unlocked"]),
    )


def _row_to_achievement(row: sqlite3.Row) -> Achievement:
    return Achievement(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        icon=row["icon"],
    )


def _row_to_unlocked(row: sqlite3.Row) -> UnlockedAchievement:
    return UnlockedAchievement(
        achievement_id=row["achievement_id"],
        profile_id=row["profile_id"],
        unlocked_at=_str_to_dt(row["unlocked_at"]) or utcnow(),
    )


class DataStore:
    """Facade over an open connection exposing all repositories."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.profiles = SqliteProfileRepository(conn)
        self.attempts = SqliteAttemptRepository(conn)
        self.progress = SqliteProgressRepository(conn)
        self.achievements = SqliteAchievementRepository(conn)

    @classmethod
    def open(cls, path: Optional[Path | str] = None) -> "DataStore":
        return cls(connect(path))

    def close(self) -> None:
        self.conn.close()
