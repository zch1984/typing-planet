"""Visual theme definitions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    theme_id: str = "space"
    name: str = "太空"

    bg_top: str = "#0b1320"
    bg_bottom: str = "#15263b"

    panel: str = "#1b263b"
    panel_alt: str = "#243756"
    border: str = "#3a4a6b"

    text: str = "#e6e8ee"
    text_dim: str = "#9aa3b2"

    correct: str = "#4ecca3"
    incorrect: str = "#e63946"
    pending: str = "#5a6473"
    current_bg: str = "#ffd166"
    current_fg: str = "#0b1320"

    accent: str = "#06d6a0"
    accent2: str = "#48cae4"
    highlight: str = "#2a3b5c"

    star: str = "#ffd166"
    star_empty: str = "#3a4756"
    lock: str = "#8d99ae"

    title_size: int = 56
    heading_size: int = 34
    body_size: int = 26
    small_size: int = 20
    keyboard_size: int = 22
    typing_size: int = 44

    @property
    def bg_gradient(self) -> tuple[str, str]:
        return (self.bg_top, self.bg_bottom)


def default_theme() -> Theme:
    return Theme()
