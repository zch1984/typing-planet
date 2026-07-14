from typingplanet.plugins.loader import build_registry


def test_pinyin_provider_present():
    r = build_registry()
    p = r.get_lesson_provider("pinyin")
    assert p is not None
    assert p.name == "一年级语文"


def test_pinyin_lessons_show_chinese_type_pinyin():
    r = build_registry()
    lessons = r.subject_lessons("pinyin")
    assert len(lessons) >= 5
    for lesson in lessons:
        assert lesson.has_display, lesson.title
        assert lesson.display_text  # Chinese characters shown
        # the typed target is plain lowercase ascii pinyin
        assert lesson.full_text.isascii(), lesson.title
        assert lesson.full_text == lesson.full_text.lower(), lesson.title


def test_pinyin_first_lesson_is_tiandiren():
    r = build_registry()
    l0 = r.subject_lessons("pinyin")[0]
    assert "天" in l0.display_text
    assert l0.full_text == "tian di ren"


def test_basic_and_pinyin_are_separate_subjects():
    r = build_registry()
    ids = {p.provider_id for p in r.lesson_providers()}
    assert {"basic", "case", "pinyin"} == ids
