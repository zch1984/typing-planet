import pytest

from typingplanet.services.typing import KeyResult, TypingSession


def test_correct_input_advances():
    s = TypingSession("abc")
    assert s.input("a", 0.0) == KeyResult.CORRECT
    assert s.position == 1
    assert s.input("b", 0.1) == KeyResult.CORRECT
    assert s.input("c", 0.2) == KeyResult.CORRECT
    assert s.is_complete


def test_wrong_key_blocking_does_not_advance():
    s = TypingSession("abc")
    assert s.input("x", 0.0) == KeyResult.INCORRECT
    assert s.position == 0
    assert s.error_count == 1
    assert s.input("a", 0.1) == KeyResult.CORRECT
    assert s.position == 1


def test_accuracy_and_wpm():
    s = TypingSession("abcd")
    s.input("a", 0.0)
    s.input("x", 0.5)  # wrong
    s.input("b", 1.0)
    s.input("c", 1.5)
    s.input("d", 2.0)
    st = s.statistics()
    assert st.correct_chars == 4
    assert st.error_chars == 1
    assert st.accuracy == pytest.approx(4 / 5)
    assert st.duration_s == pytest.approx(2.0)
    assert st.wpm == pytest.approx(24.0)


def test_complete_ignores_extra():
    s = TypingSession("ab")
    s.input("a", 0.0)
    s.input("b", 0.1)
    assert s.is_complete
    assert s.input("c", 0.2) == KeyResult.IGNORED


def test_empty_target_raises():
    with pytest.raises(ValueError):
        TypingSession("")


def test_newline_handling():
    s = TypingSession("a\nb")
    s.input("a", 0.0)
    assert s.expected_char() == "\n"
    assert s.input("\n", 0.1) == KeyResult.CORRECT
    assert s.input("b", 0.2) == KeyResult.CORRECT
    assert s.is_complete


def test_zero_state_before_start():
    s = TypingSession("ab")
    assert s.duration == 0.0
    assert s.wpm == 0.0
    assert s.accuracy == 0.0
    assert not s.is_started
