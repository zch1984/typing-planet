"""Typing-text rendering with per-character colouring and wrapping.

The layout places every character individually so the scene can highlight the
current cursor position and anchor particle effects to exact glyph rects.
"""
from __future__ import annotations

from typing import Sequence

import pygame

CharRect = tuple[int, int, int, int]  # x, y, w, h


def layout_text(font: pygame.font.Font, text: str, max_width: int,
                line_height: int) -> tuple[list[CharRect], tuple[int, int]]:
    rects: list[CharRect] = []
    x = 0
    y = 0
    max_x = 0
    for ch in text:
        if ch == "\n":
            rects.append((x, y, 0, line_height))
            max_x = max(max_x, x)
            y += line_height
            x = 0
            continue
        w, _h = font.size(ch)
        if x + w > max_width and x > 0:
            max_x = max(max_x, x)
            y += line_height
            x = 0
        rects.append((x, y, w, line_height))
        x += w
    max_x = max(max_x, x)
    total_h = y + line_height
    return rects, (max_x, total_h)


def _char_color(i: int, position: int, colors: dict[str, pygame.Color]) -> pygame.Color:
    if i == position:
        return colors["current"]
    if i < position:
        return colors["correct"]
    return colors["pending"]


def render_text(font: pygame.font.Font, text: str, position: int,
                colors: dict[str, pygame.Color], max_width: int,
                line_height: int) -> tuple[pygame.Surface, list[CharRect], tuple[int, int]]:
    rects, size = layout_text(font, text, max_width, line_height)
    w, h = size
    surface = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    for i, ch in enumerate(text):
        if ch == "\n":
            continue
        rx, ry, _cw, _ch = rects[i]
        glyph = font.render(ch, True, _char_color(i, position, colors))
        surface.blit(glyph, (rx, ry))
    return surface, rects, size
