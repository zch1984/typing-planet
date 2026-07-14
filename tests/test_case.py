"""Tests for the English uppercase/lowercase correspondence provider."""
from typingplanet.plugins.loader import build_registry
from typingplanet.services.typing import KeyResult


def test_case_provider_present():
    r = build_registry()
    p = r.get_lesson_provider("case")
    assert p is not None
    assert p.name == "大小写练习"


def test_case_lessons_count_and_order():
    r = build_registry()
    lessons = r.subject_lessons("case")
    assert len(lessons) == 8
    assert lessons == sorted(lessons, key=lambda l: (l.order, l.id))


def test_case_all_ids_unique():
    r = build_registry()
    lessons = r.subject_lessons("case")
    ids = [l.id for l in lessons]
    assert len(ids) == len(set(ids))


def test_pair_drills_have_no_display():
    r = build_registry()
    pairs = [l for l in r.subject_lessons("case") if "pair" in l.tags]
    assert len(pairs) == 3
    for lesson in pairs:
        assert not lesson.has_display
        for seg in lesson.segments:
            for token in seg.text.split():
                assert len(token) == 2, token
                assert token[0].isupper(), token
                assert token[1].islower(), token
                assert token[0].lower() == token[1], token


def test_convert_drills_have_display_with_inverse_case():
    r = build_registry()
    converts = [l for l in r.subject_lessons("case") if "convert" in l.tags]
    assert len(converts) == 4
    for lesson in converts:
        assert lesson.has_display
        display = lesson.display_text.replace(" ", "")
        text = lesson.full_text.replace(" ", "")
        assert len(display) == len(text)
        for d, t in zip(display, text):
            assert d.lower() == t.lower()
            assert d != t
            assert (d.isupper() and t.islower()) or (d.islower() and t.isupper())


def test_upper_to_lower_drills():
    r = build_registry()
    ul = [l for l in r.subject_lessons("case") if l.id.startswith("case:upper-lower")]
    assert len(ul) == 2
    for lesson in ul:
        assert lesson.display_text.replace(" ", "").isupper()
        assert lesson.full_text.replace(" ", "").islower()


def test_lower_to_upper_drills():
    r = build_registry()
    lu = [l for l in r.subject_lessons("case") if l.id.startswith("case:lower-upper")]
    assert len(lu) == 2
    for lesson in lu:
        assert lesson.display_text.replace(" ", "").islower()
        assert lesson.full_text.replace(" ", "").isupper()


def test_case_words_lesson():
    r = build_registry()
    lesson = r.get_lesson("case:words")
    assert lesson is not None
    assert "word" in lesson.tags
    for seg in lesson.segments:
        for word in seg.text.split():
            assert word[0].isupper()
            assert word[1:].islower()


def test_pair_session_completes():
    r = build_registry()
    lesson = r.get_lesson("case:pair-ah")
    assert lesson is not None
    mode = r.get_game_mode(None)
    session = mode.build_session(lesson)
    assert session.expected_char() == "A"
    for ch in lesson.full_text:
        assert session.input(ch, 0.0) == KeyResult.CORRECT
    assert session.is_complete
    assert session.error_count == 0


def test_convert_session_completes():
    r = build_registry()
    lesson = r.get_lesson("case:upper-lower-1")
    assert lesson is not None
    mode = r.get_game_mode(None)
    session = mode.build_session(lesson)
    assert session.expected_char() == "a"
    for ch in lesson.full_text:
        assert session.input(ch, 0.0) == KeyResult.CORRECT
    assert session.is_complete
