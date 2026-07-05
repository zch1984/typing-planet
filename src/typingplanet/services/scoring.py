"""Star scoring.

Accuracy is the primary driver of stars; an optional WPM floor can gate the top
rating. Thresholds are per-difficulty so harder content is judged more leniently
on speed but still rewards precision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..domain.models import Difficulty


@dataclass(frozen=True)
class StarThresholds:
    one_star: float
    two_star: float
    three_star: float
    three_star_wpm_floor: float = 0.0


DEFAULT_THRESHOLDS: Mapping[Difficulty, StarThresholds] = {
    Difficulty.EASY: StarThresholds(0.60, 0.80, 0.95),
    Difficulty.MEDIUM: StarThresholds(0.65, 0.82, 0.93),
    Difficulty.HARD: StarThresholds(0.70, 0.85, 0.95),
}


def compute_stars(
    accuracy: float,
    wpm: float = 0.0,
    difficulty: Difficulty = Difficulty.EASY,
    thresholds: Mapping[Difficulty, StarThresholds] | None = None,
) -> int:
    table = thresholds or DEFAULT_THRESHOLDS
    t = table.get(difficulty, table[Difficulty.EASY])
    if accuracy >= t.three_star and wpm >= t.three_star_wpm_floor:
        return 3
    if accuracy >= t.two_star:
        return 2
    if accuracy >= t.one_star:
        return 1
    return 0
