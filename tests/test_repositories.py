from typingplanet.data.sqlite_repositories import DataStore
from typingplanet.domain.models import Achievement


def test_profile_crud(tmp_path):
    store = DataStore.open(tmp_path / "t.db")
    p = store.profiles.create("A")
    assert store.profiles.get(p.id).name == "A"
    assert len(store.profiles.list_all()) == 1
    store.profiles.create("B")
    assert len(store.profiles.list_all()) == 2
    assert store.profiles.delete(p.id) is True
    assert store.profiles.get(p.id) is None
    assert store.attempts.list_by_profile(p.id) == []


def test_achievement_unlock_idempotent(tmp_path):
    store = DataStore.open(tmp_path / "t.db")
    store.achievements.register_definition(Achievement(id="a1", name="First"))
    p = store.profiles.create("k")
    ua = store.achievements.unlock(p.id, "a1")
    assert ua is not None
    assert store.achievements.unlock(p.id, "a1") is None
    assert store.achievements.is_unlocked(p.id, "a1")
    assert len(store.achievements.list_unlocked(p.id)) == 1


def test_attempt_repository(tmp_path):
    store = DataStore.open(tmp_path / "t.db")
    p = store.profiles.create("k")
    from typingplanet.domain.models import AttemptResult, utcnow
    r = AttemptResult(profile_id=p.id, lesson_id="keys:fj", wpm=20, accuracy=0.9,
                      correct_chars=5, error_chars=1, duration_s=15, stars=2,
                      completed_at=utcnow())
    store.attempts.add(r)
    assert store.attempts.count_for_lesson(p.id, "keys:fj") == 1
    best = store.attempts.best_for_lesson(p.id, "keys:fj")
    assert best.stars == 2
