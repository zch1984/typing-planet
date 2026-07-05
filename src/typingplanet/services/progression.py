"""Lesson progression and unlock logic.

Lessons are unlocked sequentially: the first ``initial_unlock_count`` are open
by default, and each subsequent lesson unlocks once the previous one earns at
least ``required_stars``. State is mirrored into the progress table so the UI
can query unlock state cheaply.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from ..domain.models import AttemptResult, Lesson, LessonProgress


class ProgressionService:
    def __init__(
        self,
        progress_repo,
        attempt_repo=None,
        *,
        initial_unlock_count: int = 3,
        required_stars: int = 1,
    ) -> None:
        self.progress_repo = progress_repo
        self.attempt_repo = attempt_repo
        self.initial_unlock_count = initial_unlock_count
        self.required_stars = required_stars

    def _ordered(self, lessons: Sequence[Lesson]) -> list[Lesson]:
        return sorted(lessons, key=lambda l: (l.order, l.id))

    def unlock_state(self, profile_id: str, lessons: Sequence[Lesson]) -> dict[str, bool]:
        ordered = self._ordered(lessons)
        state: dict[str, bool] = {}
        for idx, lesson in enumerate(ordered):
            if idx < self.initial_unlock_count:
                state[lesson.id] = True
                continue
            prev = ordered[idx - 1]
            p = self.progress_repo.get(profile_id, prev.id)
            state[lesson.id] = p is not None and p.best_stars >= self.required_stars
        return state

    def refresh_unlocks(self, profile_id: str, lessons: Sequence[Lesson]) -> None:
        state = self.unlock_state(profile_id, lessons)
        for lesson_id, unlocked in state.items():
            existing = self.progress_repo.get(profile_id, lesson_id)
            if existing is None:
                if unlocked:
                    self.progress_repo.upsert(
                        LessonProgress(profile_id=profile_id, lesson_id=lesson_id, unlocked=True)
                    )
            elif existing.unlocked != unlocked:
                self.progress_repo.upsert(replace(existing, unlocked=unlocked))

    def record_attempt(
        self,
        profile_id: str,
        lesson: Lesson,
        result: AttemptResult,
        all_lessons: Sequence[Lesson],
    ) -> LessonProgress:
        # Persist the raw attempt once, if an attempt repository is wired in.
        if self.attempt_repo is not None:
            self.attempt_repo.add(result)

        existing = self.progress_repo.get(profile_id, lesson.id)
        attempts = (existing.attempts + 1) if existing else 1
        best_wpm = max(existing.best_wpm, result.wpm) if existing else result.wpm
        best_acc = max(existing.best_accuracy, result.accuracy) if existing else result.accuracy
        best_stars = max(existing.best_stars, result.stars) if existing else result.stars
        prog = LessonProgress(
            profile_id=profile_id,
            lesson_id=lesson.id,
            best_wpm=best_wpm,
            best_accuracy=best_acc,
            best_stars=best_stars,
            attempts=attempts,
            last_played_at=result.completed_at,
            unlocked=True,
        )
        self.progress_repo.upsert(prog)
        self.refresh_unlocks(profile_id, all_lessons)
        updated = self.progress_repo.get(profile_id, lesson.id)
        return updated or prog
