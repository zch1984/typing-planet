import pytest

from typingplanet.domain.models import Difficulty
from typingplanet.services.scoring import DEFAULT_THRESHOLDS, compute_stars


def test_three_stars_easy():
    assert compute_stars(0.95, 50, Difficulty.EASY) == 3


def test_two_stars():
    assert compute_stars(0.85, 50, Difficulty.EASY) == 2


def test_one_star():
    assert compute_stars(0.65, 10, Difficulty.EASY) == 1


def test_zero_stars():
    assert compute_stars(0.4, 5, Difficulty.EASY) == 0


def test_boundaries_use_thresholds():
    t = DEFAULT_THRESHOLDS[Difficulty.EASY]
    assert compute_stars(t.three_star, 0, Difficulty.EASY) == 3
    assert compute_stars(t.two_star, 0, Difficulty.EASY) == 2
    assert compute_stars(t.one_star, 0, Difficulty.EASY) == 1
    just_below = t.one_star - 0.001
    assert compute_stars(just_below, 0, Difficulty.EASY) == 0


def test_harder_difficulty_uses_own_thresholds():
    t = DEFAULT_THRESHOLDS[Difficulty.HARD]
    assert compute_stars(t.three_star, 0, Difficulty.HARD) == 3
