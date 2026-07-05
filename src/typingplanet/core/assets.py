"""Font and asset loading with caching."""
from __future__ import annotations

from typing import Optional

import pygame

# CJK-capable font stack: prefer Microsoft YaHei / SimHei on Windows, then
# common cross-platform fallbacks. pygame picks the first available.
_FONT_STACK = "microsoftyahei,microsoftyaheilight,simhei,msyh,pingfangsc,hiraginosansgb,notosanscjksc,wenquanyimicrohei,dejavusans,arial"


class AssetManager:
    def __init__(self) -> None:
        self._font_cache: dict[tuple[int, bool], pygame.font.Font] = {}
        self._name: Optional[str] = None

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        f = self._font_cache.get(key)
        if f is None:
            f = pygame.font.SysFont(_FONT_STACK, size, bold=bold)
            self._font_cache[key] = f
        return f

    def resolved_font_name(self) -> str:
        if self._name is None:
            self._name = pygame.font.match_font(_FONT_STACK.replace(",", ","))
        return self._name or _FONT_STACK
