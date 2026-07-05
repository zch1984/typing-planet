"""Twinkling starfield background for the space theme."""
from __future__ import annotations

import random

import pygame


class Starfield:
    def __init__(self, width: int, height: int, count: int = 130) -> None:
        self.width = width
        self.height = height
        self.stars: list[list[float]] = [
            [random.uniform(0, width), random.uniform(0, height),
             random.uniform(0.3, 1.0), random.uniform(0.5, 2.0),
             random.uniform(0, 6.28)]
            for _ in range(count)
        ]

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def update(self, dt: float) -> None:
        for s in self.stars:
            s[4] += dt * s[3]

    def draw(self, surface: pygame.Surface) -> None:
        for s in self.stars:
            x, y, base, _spd, phase = s
            tw = 0.6 + 0.4 * (0.5 + 0.5 * (phase % 6.28) / 6.28)
            b = max(0, min(255, int(255 * base * tw)))
            r = 1 if base < 0.7 else 2
            pygame.draw.circle(surface, (b, b, b), (int(x), int(y)), r)
