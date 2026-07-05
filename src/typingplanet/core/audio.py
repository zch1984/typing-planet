"""Procedural sound synthesis (no audio files needed).

Short tones are synthesised as 16-bit PCM WAV bytes with the stdlib ``wave``
module and wrapped in ``pygame.mixer.Sound`` objects. This keeps the game fully
self-contained and easy to package.
"""
from __future__ import annotations

import io
import math
import wave
from array import array
from typing import Optional

import pygame


SAMPLE_RATE = 44100


def _env(i: int, n: int, attack: float, release: float) -> float:
    t = i / n
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = min(1.0, (1.0 - t) / release) if release > 0 else 1.0
    return max(0.0, min(a, r))


def _tone(freq: float, duration: float, volume: float = 0.5,
          attack: float = 0.02, release: float = 0.25,
          harmonics: tuple[float, ...] = (1.0,)) -> bytes:
    n = max(1, int(duration * SAMPLE_RATE))
    samples = array("h")
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics, start=1):
            s += h_amp * math.sin(2 * math.pi * freq * h_idx * t)
        s /= max(1, len(harmonics))
        val = int(32767 * volume * _env(i, n, attack, release) * s)
        samples.append(max(-32768, min(32767, val)))
    return _wav_bytes(samples.tobytes())


def _silence(duration: float) -> bytes:
    n = max(1, int(duration * SAMPLE_RATE))
    return _wav_bytes(array("h", [0] * n).tobytes())


def _wav_bytes(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def _concat(chunks: list[bytes]) -> bytes:
    # All chunks share the same WAV header params; strip headers and rebuild.
    pcm = bytearray()
    for c in chunks:
        with wave.open(io.BytesIO(c), "rb") as r:
            pcm.extend(r.readframes(r.getnframes()))
    return _wav_bytes(bytes(pcm))


def _build_library() -> dict[str, bytes]:
    return {
        "key_correct": _tone(880.0, 0.06, volume=0.35, attack=0.005, release=0.12),
        "key_wrong": _tone(150.0, 0.14, volume=0.45, attack=0.005, release=0.2,
                           harmonics=(1.0, 0.5, 0.25)),
        "complete": _concat([
            _tone(523.25, 0.12, volume=0.4, release=0.3),
            _tone(659.25, 0.12, volume=0.4, release=0.3),
            _tone(783.99, 0.22, volume=0.45, release=0.4),
        ]),
        "star": _tone(1046.5, 0.18, volume=0.4, release=0.3),
    }


class AudioManager:
    def __init__(self, enabled: bool = True, volume: float = 0.7) -> None:
        self._enabled = enabled
        self._volume = volume
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._available = False

    def init(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=256)
            self._available = True
            for name, data in _build_library().items():
                try:
                    snd = pygame.mixer.Sound(buffer=data)
                    snd.set_volume(self._volume)
                    self._sounds[name] = snd
                except Exception:
                    pass
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        for snd in self._sounds.values():
            snd.set_volume(self._volume)

    def play(self, name: str) -> None:
        if not self._enabled or not self._available:
            return
        snd = self._sounds.get(name)
        if snd is not None:
            snd.play()
