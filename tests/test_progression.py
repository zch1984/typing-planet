import pytest

from typingplanet.domain.models import AttemptResult, utcnow
from typingplanet.data.sqlite_repositories import DataStore
from typingplanet.plugins.loader import build_registry
from typingplanet.services.progression import ProgressionService


@pytest.fixture
def lessons():
    return build_registry().all_lessons()


def test_initial_unlock_count(tmp_path, lessons):
    store = DataStore.open(tmp_path / "t.db")
    p = store.profiles.create("kid")
    svc = ProgressionService(store.progress, store.attempts)
    state = svc.unlock_state(p.id, lessons)
    assert sum(state.values()) == svc.initial_unlock_count


def test_record_attempt_updates_best_and_unlocks_next(tmp_path, lessons):
    store = DataStore.open(tmp_path / "t.db")
    p = store.profiles.create("kid")
    svc = ProgressionService(store.progress, store.attempts)
    l0 = lessons[0]
    res = AttemptResult(
        profile_id=p.id, lesson_id=l0.id, wpm=30, accuracy=0.95,
        correct_chars=5, error_chars=0, duration_s=10, stars=3,
        completed_at=utcnow(),
    )
    prog = svc.record_attempt(p.id, l0, res, lessons)
    assert prog.best_stars == 3
    assert prog.attempts == 1
    state = svc.unlock_state(p.id, lessons)
    assert state[lessons[1].id] is True
    assert store.attempts.best_for_lesson(p.id, l0.id).stars == 3


def test_keeps_best_across_attempts(tmp_path, lessons):
    store = DataStore.open(tmp_path / "t.db")
    p = store.profiles.create("kid")
    svc = ProgressionService(store.progress, store.attempts)
    l0 = lessons[0]
    good = AttemptResult(profile_id=p.id, lesson_id=l0.id, wpm=30, accuracy=0.95,
                         correct_chars=5, error_chars=0, duration_s=10, stars=3,
                         completed_at=utcnow())
    svc.record_attempt(p.id, l0, good, lessons)
    worse = AttemptResult(profile_id=p.id, lesson_id=l0.id, wpm=10, accuracy=0.6,
                          correct_chars=5, error_chars=3, duration_s=20, stars=1,
                          completed_at=utcnow())
    svc.record_attempt(p.id, l0, worse, lessons)
    prog = store.progress.get(p.id, l0.id)
    assert prog.best_stars == 3
    assert prog.best_wpm == 30
    assert prog.attempts == 2
