"""Reusable UI widgets: buttons, star rating, progress bar, virtual keyboard."""
from __future__ import annotations

import math
from typing import Callable, Optional, Sequence

import pygame

from ..core.theme import Theme


def lerp_color(a: pygame.Color, b: pygame.Color, t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a.r + (b.r - a.r) * t),
        int(a.g + (b.g - a.g) * t),
        int(a.b + (b.b - a.b) * t),
    )


def rounded_rect(surface: pygame.Surface, color, rect: pygame.Rect,
                 radius: int = 10, width: int = 0) -> None:
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


class Button:
    def __init__(self, rect, label: str, callback: Optional[Callable] = None, *,
                 font: Optional[pygame.font.Font] = None, style: str = "primary",
                 enabled: bool = True) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.font = font
        self.style = style
        self.enabled = enabled
        self.hover = False
        self.pressed = False
        self._hover_anim = 0.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.pressed
            self.pressed = False
            if was and self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def update(self, dt: float) -> None:
        target = 1.0 if (self.hover and self.enabled) else 0.0
        self._hover_anim += (target - self._hover_anim) * min(1.0, dt * 14)

    def draw(self, surface: pygame.Surface, theme: Theme) -> None:
        base = {
            "primary": pygame.Color(theme.accent),
            "secondary": pygame.Color(theme.panel_alt),
            "ghost": pygame.Color(theme.panel),
            "danger": pygame.Color(theme.incorrect),
        }[self.style]
        bright = pygame.Color(min(255, base.r + 40), min(255, base.g + 40), min(255, base.b + 40))
        col = lerp_color(base, bright, self._hover_anim)
        if not self.enabled:
            col = (col[0] // 2 + 30, col[1] // 2 + 30, col[2] // 2 + 30)

        offset = 2 if (self.pressed and self.enabled) else 0
        r = self.rect.move(0, offset)
        # subtle shadow
        shadow = self.rect.move(0, 4)
        s = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 70), s.get_rect(), border_radius=12)
        surface.blit(s, shadow.topleft)
        rounded_rect(surface, col, r, radius=12)
        border = pygame.Color(theme.border) if self.enabled else pygame.Color(theme.lock)
        rounded_rect(surface, border, r, radius=12, width=2)

        font = self.font
        if font is None:
            font = pygame.font.SysFont("arial", 22)
        text_col = theme.current_fg if self.style == "primary" and self.enabled else theme.text
        if not self.enabled:
            text_col = theme.text_dim
        label = font.render(self.label, True, text_col)
        surface.blit(label, label.get_rect(center=r.center))


def star_points(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.45
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts


def draw_stars(surface: pygame.Surface, cx: int, cy: int, filled: int, total: int = 3,
               r: int = 16, gap: int = 26, theme: Optional[Theme] = None) -> None:
    theme = theme or Theme()
    total_w = (total - 1) * gap
    start_x = cx - total_w / 2
    for i in range(total):
        x = start_x + i * gap
        col = pygame.Color(theme.star) if i < filled else pygame.Color(theme.star_empty)
        pygame.draw.polygon(surface, col, star_points(x, cy, r))


def draw_progress(surface: pygame.Surface, rect: pygame.Rect, fraction: float,
                  theme: Theme) -> None:
    fraction = max(0.0, min(1.0, fraction))
    rounded_rect(surface, theme.panel, rect, radius=rect.height // 2)
    if fraction > 0:
        fill = rect.copy()
        fill.w = int(rect.w * fraction)
        rounded_rect(surface, theme.accent, fill, radius=rect.height // 2)


# --------------------------------------------------------------------------- #
# Virtual keyboard
# --------------------------------------------------------------------------- #

_ROWS: tuple[str, ...] = (
    "1234567890-=",
    "qwertyuiop[]",
    "asdfghjkl;'",
    "zxcvbnm,./",
)
_HOME_KEYS = {"f", "j"}


class VirtualKeyboard:
    """A simple QWERTY keyboard that can highlight the next key to press."""

    def __init__(self) -> None:
        self.keys: list[dict] = []  # each: {label, char, rect, home}

    def layout(self, x: int, y: int, key_w: int = 52, key_h: int = 52,
               gap: int = 6, width: int = 1100) -> None:
        self.keys = []
        rows = list(_ROWS) + [" "]
        max_len = max(len(r) if r != " " else 10 for r in _ROWS)
        for row in rows:
            if row == " ":
                # space bar row
                w = key_w * 6 + gap * 5
                rx = x + (width - w) // 2
                self.keys.append({
                    "label": "Space", "char": " ", "home": False,
                    "rect": pygame.Rect(rx, y, w, key_h),
                })
                y += key_h + gap
                continue
            row_w = len(row) * key_w + (len(row) - 1) * gap
            rx = x + (width - row_w) // 2
            for ch in row:
                label = ch.upper() if ch.isalpha() else ch
                self.keys.append({
                    "label": label, "char": ch, "home": ch in _HOME_KEYS,
                    "rect": pygame.Rect(rx, y, key_w, key_h),
                })
                rx += key_w + gap
            y += key_h + gap

    @property
    def height(self) -> int:
        if not self.keys:
            return 0
        return max(k["rect"].bottom for k in self.keys) - min(k["rect"].top for k in self.keys)

    def key_for_char(self, char: str) -> Optional[dict]:
        c = char.lower()
        for k in self.keys:
            if k["char"] == c:
                return k
        return None

    def draw(self, surface: pygame.Surface, theme: Theme,
             highlight: Optional[str] = None, font: Optional[pygame.font.Font] = None) -> None:
        font = font or pygame.font.SysFont("arial", 20, bold=True)
        highlight_key = self.key_for_char(highlight) if highlight else None
        for k in self.keys:
            r = k["rect"]
            if k is highlight_key:
                rounded_rect(surface, theme.current_bg, r, radius=8)
                label_col = theme.current_fg
            elif k["home"]:
                rounded_rect(surface, theme.panel_alt, r, radius=8)
                label_col = theme.text
            else:
                rounded_rect(surface, theme.panel, r, radius=8)
                label_col = theme.text_dim
            rounded_rect(surface, theme.border, r, radius=8, width=1)
            if k["home"] and k is not highlight_key:
                pygame.draw.circle(surface, theme.accent2, (r.centerx, r.bottom - 7), 2)
            label = font.render(k["label"], True, label_col)
            surface.blit(label, label.get_rect(center=r.center))
