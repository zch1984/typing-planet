from typingplanet.plugins.loader import build_registry
from typingplanet.services.typing import KeyResult, TypingSession


def test_registry_has_builtins():
    r = build_registry()
    assert {p.provider_id for p in r.lesson_providers()} == {"basic", "case", "pinyin"}
    assert r.get_game_mode(None).mode_id == "classic"
    assert r.get_reward_strategy(None).strategy_id == "default"
    lessons = r.all_lessons()
    assert lessons == sorted(lessons, key=lambda l: (l.order, l.id))
    assert r.get_lesson(lessons[0].id) is not None


def test_subject_lessons_per_provider():
    r = build_registry()
    basic = r.subject_lessons("basic")
    pinyin = r.subject_lessons("pinyin")
    assert basic and pinyin
    assert {l.provider_id for l in basic} == {"basic"}
    assert {l.provider_id for l in pinyin} == {"pinyin"}
    assert basic == sorted(basic, key=lambda l: (l.order, l.id))


def test_reward_events_on_key():
    r = build_registry()
    rs = r.get_reward_strategy(None)
    s = TypingSession("ab")
    s.input("a", 0.0)
    ev = rs.on_key(KeyResult.CORRECT, s.statistics())
    assert any(e.name == "key_correct" for e in ev)


def test_reward_events_on_complete_three_stars():
    r = build_registry()
    rs = r.get_reward_strategy(None)
    s = TypingSession("ab")
    s.input("a", 0.0)
    s.input("b", 0.1)
    ev = rs.on_complete(s.statistics(), 3)
    kinds = {type(e).__name__ for e in ev}
    assert "BurstEvent" in kinds
    assert "TextEvent" in kinds
