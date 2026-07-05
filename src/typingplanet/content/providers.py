"""Built-in lesson providers, game mode and reward strategy."""
from __future__ import annotations

from typing import Sequence

from ..domain.models import Difficulty, Lesson, Segment
from ..plugins.contracts import (
    BurstEvent,
    GameMode,
    LessonProvider,
    RewardStrategy,
    SoundEvent,
    TextEvent,
)
from ..services.typing import KeyResult, TypingSession, TypingStatistics


def _lesson(
    provider_id: str,
    lid: str,
    title: str,
    description: str,
    difficulty: Difficulty,
    order: int,
    lines: Sequence[str],
    tags: Sequence[str] = (),
) -> Lesson:
    return Lesson(
        id=f"{lid}",
        provider_id=provider_id,
        title=title,
        description=description,
        difficulty=difficulty,
        segments=tuple(Segment(text=line) for line in lines),
        order=order,
        tags=tuple(tags),
    )


def _pinyin_lesson(lid: str, title: str, chinese: str, pinyin: str, order: int) -> Lesson:
    return Lesson(
        id=lid,
        provider_id="pinyin",
        title=title,
        description="看汉字，打拼音",
        difficulty=Difficulty.MEDIUM,
        segments=(Segment(text=pinyin, display=chinese),),
        order=order,
        tags=("pinyin", "grade1"),
    )


# --------------------------------------------------------------------------- #
# Basic training (keys + words)
# --------------------------------------------------------------------------- #


class BasicTrainingProvider:
    """Letter-key drills and word/sentence drills."""

    provider_id = "basic"
    name = "基础训练"

    def __init__(self) -> None:
        keys = [
            _lesson("basic", "keys:fj", "F 与 J", "食指定位键", Difficulty.EASY, 1,
                    ["fj fj fj", "jf jf jf", "ff jj ff jj"], tags=("home",)),
            _lesson("basic", "keys:dk", "D 与 K", "食指上移", Difficulty.EASY, 2,
                    ["dk dk dk", "kd kd kd", "dd kk dd kk"], tags=("home",)),
            _lesson("basic", "keys:sl", "S 与 L", "无名指", Difficulty.EASY, 3,
                    ["sl sl sl", "ls ls ls", "ss ll ss ll"], tags=("home",)),
            _lesson("basic", "keys:a-semi", "A 与 分号", "小指定位", Difficulty.EASY, 4,
                    ["a; a; a;", ";a ;a ;a", "aa ;; aa ;;"], tags=("home",)),
            _lesson("basic", "keys:home-row", "主键位行", "asdf jkl;", Difficulty.EASY, 5,
                    ["asdf jkl;", "asdf jkl;", "fdsa ;lkj", "jkl; asdf"], tags=("home",)),
            _lesson("basic", "keys:top-row", "上排键", "qwer uiop", Difficulty.EASY, 6,
                    ["qwer uiop", "qwer uiop", "rewq poi u", "t y t y gh gh"], tags=("top",)),
            _lesson("basic", "keys:bottom-row", "下排键", "zxcv nm,.", Difficulty.EASY, 7,
                    ["zxcv bn m", "zxcv bn m", "vcxz mnb ", "z x c v b n m ,"], tags=("bottom",)),
            _lesson("basic", "keys:alphabet", "全部字母", "26 letters", Difficulty.EASY, 8,
                    ["abcdefgh", "ijklmnop", "qrstuvwx", "yz yz yz"], tags=("alpha",)),
            _lesson("basic", "words:short", "短单词", "三字母词", Difficulty.MEDIUM, 9,
                    ["cat dog sun", "hat bat mat", "red bed leg", "big pig dig"]),
            _lesson("basic", "words:common", "常用词", "高频词", Difficulty.MEDIUM, 10,
                    ["the and you for", "with his they this", "have from or one", "not but what all"]),
            _lesson("basic", "words:animals", "动物", "英文动物名", Difficulty.MEDIUM, 11,
                    ["cat dog bird fish", "lion tiger bear wolf", "rabbit monkey panda", "horse sheep duck frog"]),
            _lesson("basic", "words:sentences", "短句子", "简单句", Difficulty.HARD, 12,
                    ["i can see a cat", "the sun is red", "my dog is big", "i like to read"]),
        ]
        self._lessons = keys
        self._by_id = {l.id: l for l in self._lessons}

    def lessons(self) -> Sequence[Lesson]:
        return list(self._lessons)

    def get_lesson(self, lesson_id: str) -> Lesson | None:
        return self._by_id.get(lesson_id)


# --------------------------------------------------------------------------- #
# Grade-1 Chinese pinyin
# --------------------------------------------------------------------------- #


class PinyinProvider:
    """一年级语文：看汉字，打拼音（无声调，音节间用空格）。"""

    provider_id = "pinyin"
    name = "一年级语文"

    def __init__(self) -> None:
        self._lessons: list[Lesson] = [
            _pinyin_lesson("pinyin:tiandiren", "天地人", "天 地 人", "tian di ren", 1),
            _pinyin_lesson("pinyin:niwota", "你我他", "你 我 他", "ni wo ta", 2),
            _pinyin_lesson("pinyin:yiersan", "一二三", "一 二 三", "yi er san", 3),
            _pinyin_lesson("pinyin:siwuliu", "四五六", "四 五 六", "si wu liu", 4),
            _pinyin_lesson("pinyin:qibajiu", "七八九", "七 八 九", "qi ba jiu", 5),
            _pinyin_lesson("pinyin:shangxiazuoyou", "上下左右", "上 下 左 右", "shang xia zuo you", 6),
            _pinyin_lesson("pinyin:riyueshuihuo", "日月水火", "日 月 水 火", "ri yue shui huo", 7),
            _pinyin_lesson("pinyin:shanshitiantu", "山石田土", "山 石 田 土", "shan shi tian tu", 8),
            _pinyin_lesson("pinyin:daxiaoduoshao", "大小多少", "大 小 多 少", "da xiao duo shao", 9),
            _pinyin_lesson("pinyin:bamahao", "爸妈好", "爸 妈 好", "ba ma hao", 10),
        ]
        self._by_id = {l.id: l for l in self._lessons}

    def lessons(self) -> Sequence[Lesson]:
        return list(self._lessons)

    def get_lesson(self, lesson_id: str) -> Lesson | None:
        return self._by_id.get(lesson_id)


# --------------------------------------------------------------------------- #
# Game mode
# --------------------------------------------------------------------------- #


class ClassicGameMode:
    """Plain blocking typing of the full lesson text."""

    mode_id = "classic"
    name = "经典模式"
    description = "逐字打字，按对才前进"

    def build_session(self, lesson: Lesson) -> TypingSession:
        return TypingSession(lesson.full_text)

    def is_finished(self, session: TypingSession) -> bool:
        return session.is_complete


# --------------------------------------------------------------------------- #
# Reward strategy
# --------------------------------------------------------------------------- #


class DefaultRewardStrategy:
    strategy_id = "default"

    def on_key(self, result: KeyResult, stats: TypingStatistics):
        if result == KeyResult.CORRECT:
            return [SoundEvent("key_correct")]
        if result == KeyResult.INCORRECT:
            return [SoundEvent("key_wrong")]
        return []

    def on_complete(self, stats: TypingStatistics, stars: int):
        events = [SoundEvent("complete"), BurstEvent("center", "gold", 28)]
        if stars >= 2:
            events.append(BurstEvent("cursor", "cyan", 18))
        if stars >= 3:
            events.append(TextEvent("Perfect!", "gold"))
        return events
