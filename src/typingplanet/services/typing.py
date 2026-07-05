"""Core typing evaluation logic.

``TypingSession`` runs in *blocking mode*: the cursor only advances on a
correct keypress, and wrong keys are counted as errors without moving the
cursor. This gives immediate per-key feedback and is well suited to children
learning the keyboard. The session is engine-agnostic -- it consumes plain
characters and timestamps, which makes it trivially unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class KeyResult(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    IGNORED = "ignored"


@dataclass
class Keystroke:
    char: str
    timestamp: float
    correct: bool


@dataclass(frozen=True)
class TypingStatistics:
    wpm: float
    accuracy: float  # 0..1
    correct_chars: int
    error_chars: int
    duration_s: float


class TypingSession:
    def __init__(self, target: str) -> None:
        if not target:
            raise ValueError("TypingSession requires a non-empty target")
        self.target = target
        self._pos = 0
        self._correct = 0
        self._errors = 0
        self._keystrokes: list[Keystroke] = []
        self._start_ts: Optional[float] = None
        self._end_ts: Optional[float] = None

    @property
    def position(self) -> int:
        return self._pos

    @property
    def correct_count(self) -> int:
        return self._correct

    @property
    def error_count(self) -> int:
        return self._errors

    @property
    def total_keystrokes(self) -> int:
        return len(self._keystrokes)

    @property
    def keystrokes(self) -> tuple[Keystroke, ...]:
        return tuple(self._keystrokes)

    @property
    def is_started(self) -> bool:
        return self._start_ts is not None

    @property
    def is_complete(self) -> bool:
        return self._pos >= len(self.target)

    @property
    def duration(self) -> float:
        if self._start_ts is None:
            return 0.0
        end = self._end_ts if self._end_ts is not None else self._start_ts
        return max(end - self._start_ts, 0.0)

    def expected_char(self) -> str:
        if self.is_complete:
            return ""
        return self.target[self._pos]

    def input(self, ch: str, timestamp: float) -> KeyResult:
        if self.is_complete or not ch:
            return KeyResult.IGNORED
        if self._start_ts is None:
            self._start_ts = timestamp
        expected = self.target[self._pos]
        if ch == expected:
            self._correct += 1
            self._pos += 1
            self._keystrokes.append(Keystroke(ch, timestamp, True))
            if self._pos >= len(self.target):
                self._end_ts = timestamp
            return KeyResult.CORRECT
        self._errors += 1
        self._keystrokes.append(Keystroke(ch, timestamp, False))
        return KeyResult.INCORRECT

    @property
    def wpm(self) -> float:
        minutes = self.duration / 60.0
        if minutes <= 0:
            return 0.0
        return (self._correct / 5.0) / minutes

    @property
    def accuracy(self) -> float:
        total = self._correct + self._errors
        if total == 0:
            return 0.0
        return self._correct / total

    def statistics(self) -> TypingStatistics:
        return TypingStatistics(
            wpm=self.wpm,
            accuracy=self.accuracy,
            correct_chars=self._correct,
            error_chars=self._errors,
            duration_s=self.duration,
        )
