"""Lightweight particle system for reward feedback."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    size: float


class ParticleSystem:
    def __init__(self, gravity: float = 260.0) -> None:
        self._particles: list[Particle] = []
        self._gravity = gravity

    @property
    def particles(self) -> list[Particle]:
        return self._particles

    def burst(self, x: float, y: float, color: tuple[int, int, int],
              count: int = 14, speed: float = 240.0) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.4, speed)
            life = random.uniform(0.35, 0.7)
            self._particles.append(Particle(
                x=x, y=y,
                vx=math.cos(angle) * spd,
                vy=math.sin(angle) * spd - 60.0,
                life=life, max_life=life,
                color=color, size=random.uniform(2.0, 4.5),
            ))

    def update(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self._particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += self._gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface) -> None:
        for p in self._particles:
            alpha = max(0.0, min(1.0, p.life / p.max_life))
            r = max(1, int(p.size * (0.5 + 0.5 * alpha)))
            col = (p.color[0], p.color[1], p.color[2], int(255 * alpha))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, col, (r, r), r)
            surface.blit(s, (p.x - r, p.y - r))
