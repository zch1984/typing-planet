"""Translate pygame KEYDOWN events into the character they represent.

The tricky part is the system IME: when a Chinese input method is active it
often swallows the character, leaving ``event.unicode`` empty while still
delivering the keycode. A typing game must keep working in that case, so we
prefer ``unicode`` (correct for the active layout when no IME is composing) and
fall back to deriving the character from the keycode + modifier state.
"""
from __future__ import annotations

import pygame

_SHIFT_DIGITS = {
    "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
    "6": "^", "7": "&", "8": "*", "9": "(", "0": ")",
}
_SYMBOLS = {
    pygame.K_MINUS: ("-", "_"),
    pygame.K_EQUALS: ("=", "+"),
    pygame.K_LEFTBRACKET: ("[", "{"),
    pygame.K_RIGHTBRACKET: ("]", "}"),
    pygame.K_SEMICOLON: (";", ":"),
    pygame.K_QUOTE: ("'", '"'),
    pygame.K_COMMA: (",", "<"),
    pygame.K_PERIOD: (".", ">"),
    pygame.K_SLASH: ("/", "?"),
    pygame.K_BACKSLASH: ("\\", "|"),
    pygame.K_BACKQUOTE: ("`", "~"),
}


def _from_keycode(event: pygame.event.Event) -> str | None:
    key = event.key
    shift = bool(event.mod & (pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT))
    caps = bool(event.mod & pygame.KMOD_CAPS)

    if pygame.K_a <= key <= pygame.K_z:
        c = chr(ord("a") + key - pygame.K_a)
        return c.upper() if (shift ^ caps) else c
    if pygame.K_0 <= key <= pygame.K_9:
        base = chr(ord("0") + key - pygame.K_0)
        return _SHIFT_DIGITS.get(base, base) if shift else base
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return "\n"
    if key == pygame.K_SPACE:
        return " "
    if key == pygame.K_BACKSPACE:
        return None
    sym = _SYMBOLS.get(key)
    if sym is not None:
        return sym[1] if shift else sym[0]
    return None


def char_from_keydown(event: pygame.event.Event) -> str | None:
    """Return the character for a KEYDOWN event, or None for non-typing keys.

    None is returned for backspace and any key we cannot map (arrows, function
    keys, etc.). Backspace is intentionally ignored in the blocking game mode.
    """
    if event.type != pygame.KEYDOWN:
        return None
    if event.key == pygame.K_BACKSPACE:
        return None
    u = event.unicode
    if u:
        if u in ("\n", "\t") or u.isprintable():
            return u
    return _from_keycode(event)
