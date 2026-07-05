import pygame

from typingplanet.core.input import char_from_keydown


def _ev(key, unicode="", mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=mod)


def test_unicode_preferred():
    assert char_from_keydown(_ev(pygame.K_f, unicode="f")) == "f"


def test_ime_empty_unicode_falls_back_to_keycode():
    assert char_from_keydown(_ev(pygame.K_f, unicode="")) == "f"
    assert char_from_keydown(_ev(pygame.K_j, unicode="")) == "j"
    assert char_from_keydown(_ev(pygame.K_a, unicode="")) == "a"


def test_enter_empty_unicode_and_carriage_return():
    assert char_from_keydown(_ev(pygame.K_RETURN, unicode="")) == "\n"
    assert char_from_keydown(_ev(pygame.K_RETURN, unicode="\r")) == "\n"


def test_space_both_paths():
    assert char_from_keydown(_ev(pygame.K_SPACE, unicode=" ")) == " "
    assert char_from_keydown(_ev(pygame.K_SPACE, unicode="")) == " "


def test_shifted_symbol_and_base_symbol():
    assert char_from_keydown(_ev(pygame.K_MINUS, unicode="", mod=pygame.KMOD_LSHIFT)) == "_"
    assert char_from_keydown(_ev(pygame.K_SEMICOLON, unicode="")) == ";"


def test_backspace_and_non_typing_keys_return_none():
    assert char_from_keydown(_ev(pygame.K_BACKSPACE, unicode="")) is None
    assert char_from_keydown(_ev(pygame.K_UP, unicode="")) is None
    assert char_from_keydown(_ev(pygame.K_F1, unicode="")) is None


def test_non_keydown_event_returns_none():
    ev = pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0), rel=(0, 0), buttons=(0, 0, 0))
    assert char_from_keydown(ev) is None
