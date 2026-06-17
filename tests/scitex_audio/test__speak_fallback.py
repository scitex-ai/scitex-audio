"""Tests for config-preferred backend selection + loud fallback (operator 2026-06-17).

The TTS fallback must obey the fail-loud doctrine: when the operator's preferred
voice is unavailable and a worse backend is used, the operator must AUDIBLY
realise it — the degraded backend speaks a short "Voice degraded: ..." prefix —
never a silent downgrade. The preferred backend is configurable via
SCITEX_AUDIO_DEFAULT_BACKEND (settable in ~/.scitex/audio/local.src).

No mocks: a hand-rolled fake TTS records the text it was asked to speak; the
backend list / order / factory are dependency-injected seams. AAA markers;
one assertion per test.
"""

from __future__ import annotations

import os

import pytest

from scitex_audio._speak import (
    _degradation_notice,
    _resolve_preferred_backend,
    _try_speak_with_fallback,
)

ORDER = ["elevenlabs", "luxtts", "gtts", "pyttsx3"]


class _FakeTTS:
    """Records the text it was asked to speak; optionally raises (to fail)."""

    def __init__(self, name, sink, fail=False):
        self._name = name
        self._sink = sink
        self._fail = fail

    def speak(self, text, voice=None, play=True, output_path=None):
        if self._fail:
            raise RuntimeError(f"{self._name} boom")
        self._sink["spoken"] = text
        return {"success": True, "played": play, "play_requested": play}


def _factory(spoken_sink, fail_set=()):
    def _make(backend, **kwargs):
        return _FakeTTS(backend, spoken_sink, fail=backend in fail_set)

    return _make


@pytest.fixture
def clean_pref_env():
    """Explicit save/restore of SCITEX_AUDIO_DEFAULT_BACKEND (no monkeypatch)."""
    key = "SCITEX_AUDIO_DEFAULT_BACKEND"
    saved = os.environ.get(key)
    os.environ.pop(key, None)
    try:
        yield key
    finally:
        if saved is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = saved


# --- _resolve_preferred_backend ---------------------------------------------


def test_preferred_defaults_to_first_available_in_order(clean_pref_env):
    # Arrange
    available = ["luxtts", "gtts", "pyttsx3"]
    # Act
    pref = _resolve_preferred_backend(available, ORDER)
    # Assert
    assert pref == "luxtts"


def test_env_overrides_preferred_when_available(clean_pref_env):
    # Arrange
    os.environ[clean_pref_env] = "gtts"
    available = ["elevenlabs", "gtts", "pyttsx3"]
    # Act
    pref = _resolve_preferred_backend(available, ORDER)
    # Assert
    assert pref == "gtts"


def test_env_preferred_ignored_when_not_available(clean_pref_env):
    # Arrange
    os.environ[clean_pref_env] = "elevenlabs"
    available = ["gtts", "pyttsx3"]
    # Act
    pref = _resolve_preferred_backend(available, ORDER)
    # Assert
    assert pref == "gtts"


# --- _degradation_notice -----------------------------------------------------


def test_no_notice_when_using_preferred():
    # Arrange
    preferred, used = "elevenlabs", "elevenlabs"
    # Act
    notice = _degradation_notice(preferred, used)
    # Assert
    assert notice == ""


def test_notice_names_both_preferred_and_used_when_degraded():
    # Arrange
    preferred, used = "elevenlabs", "gtts"
    # Act
    notice = _degradation_notice(preferred, used)
    # Assert
    assert "elevenlabs" in notice and "gtts" in notice


# --- _try_speak_with_fallback (DI seams) ------------------------------------


def test_uses_preferred_backend_first(clean_pref_env):
    # Arrange
    sink = {}
    # Act
    result, used, _ = _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts", "pyttsx3"],
        order=ORDER,
        tts_factory=_factory(sink),
    )
    # Assert
    assert used == "elevenlabs"


def test_no_degradation_prefix_when_preferred_used(clean_pref_env):
    # Arrange
    sink = {}
    # Act
    _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts"],
        order=ORDER,
        tts_factory=_factory(sink),
    )
    # Assert
    assert sink["spoken"] == "hello"


def test_degradation_prefix_spoken_when_falling_back(clean_pref_env):
    # Arrange — elevenlabs present but FAILS at call time -> falls to gtts.
    sink = {}
    # Act
    _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts"],
        order=ORDER,
        tts_factory=_factory(sink, fail_set={"elevenlabs"}),
    )
    # Assert
    assert sink["spoken"].startswith("Voice degraded:") and sink["spoken"].endswith(
        "hello"
    )


def test_result_flags_degraded_true_on_fallback(clean_pref_env):
    # Arrange
    sink = {}
    # Act
    result, used, _ = _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts"],
        order=ORDER,
        tts_factory=_factory(sink, fail_set={"elevenlabs"}),
    )
    # Assert
    assert result["degraded"] is True


def test_result_not_degraded_when_preferred_succeeds(clean_pref_env):
    # Arrange
    sink = {}
    # Act
    result, used, _ = _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts"],
        order=ORDER,
        tts_factory=_factory(sink),
    )
    # Assert
    assert result["degraded"] is False


def test_all_backends_fail_returns_none_with_errors(clean_pref_env):
    # Arrange
    sink = {}
    # Act
    result, used, errors = _try_speak_with_fallback(
        "hello",
        backends=["elevenlabs", "gtts"],
        order=ORDER,
        tts_factory=_factory(sink, fail_set={"elevenlabs", "gtts"}),
    )
    # Assert
    assert result is None and len(errors) == 2
