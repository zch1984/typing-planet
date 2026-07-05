import pygame


def _font():
    pygame.font.init()
    return pygame.font.SysFont("microsoftyahei,arial,dejavusans", 30)


def test_layout_basic():
    from typingplanet.core.render import layout_text
    f = _font()
    rects, size = layout_text(f, "abc", 1000, 40)
    assert len(rects) == 3
    assert size[0] > 0
    assert size[1] == 40


def test_layout_newline_advances_line():
    from typingplanet.core.render import layout_text
    f = _font()
    rects, _size = layout_text(f, "a\nb", 1000, 40)
    assert rects[1][2] == 0  # newline is zero-width
    assert rects[2][1] == 40  # 'b' sits on the next line


def test_layout_wraps_on_overflow():
    from typingplanet.core.render import layout_text
    f = _font()
    text = "abcdefghij" * 20
    rects, size = layout_text(f, text, 300, 40)
    assert size[1] > 40  # wrapped to multiple lines
    assert len(rects) == len(text)


def test_render_text_returns_surface():
    from typingplanet.core.render import render_text
    f = _font()
    surf, rects, size = render_text(
        f, "abc", 1,
        {"correct": pygame.Color("#4ecca3"), "pending": pygame.Color("#5a6473"),
         "current": pygame.Color("#0b1320")},
        1000, 40,
    )
    assert surf.get_width() > 0
    assert len(rects) == 3
