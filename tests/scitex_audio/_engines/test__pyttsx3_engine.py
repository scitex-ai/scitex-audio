#!/usr/bin/env python3
# Timestamp: 2026-05-23
# File: tests/scitex_audio/_engines/test__pyttsx3_engine.py

"""Tests for scitex_audio._engines._pyttsx3_engine.

Rewritten to honour the no-mocks rule. The pyttsx3 engine is the
canonical "external library with side effects" collaborator; the
production class now accepts an `engine_factory=` keyword-only
parameter that lets tests inject a hand-rolled `_FakeEngine` without
patching `sys.modules`.

Tests that previously verified `setProperty.assert_any_call(...)` are
re-shaped to assert on the fake's recorded state (`engine.properties`,
`engine.said`, etc.), which is real observable production state
rather than mock-internal accounting.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._pyttsx3_engine import SystemTTS


@dataclass
class _FakeVoice:
    name: str
    id: str
    languages: list = field(default_factory=list)


class _FakeEngine:
    """Hand-rolled fake of the pyttsx3 engine API surface used by SystemTTS."""

    def __init__(self, voices=None) -> None:
        self.properties: dict[str, Any] = {}
        self.voices = voices if voices is not None else []
        self.saved: list[tuple[str, str]] = []
        self.said: list[str] = []
        self.run_calls = 0

    def setProperty(self, name: str, value: Any) -> None:
        self.properties[name] = value

    def getProperty(self, name: str):
        if name == "voices":
            return self.voices
        return self.properties.get(name)

    def save_to_file(self, text: str, path: str) -> None:
        self.saved.append((text, path))
        # Write a placeholder so callers that check the file get something.
        Path(path).write_bytes(b"FAKE_AUDIO")

    def say(self, text: str) -> None:
        self.said.append(text)

    def runAndWait(self) -> None:
        self.run_calls += 1


def _make_tts(engine: _FakeEngine, **kwargs) -> SystemTTS:
    """Build a SystemTTS bound to a hand-rolled fake engine."""
    return SystemTTS(engine_factory=lambda: engine, **kwargs)


@pytest.fixture
def no_pyttsx3():
    """Hide pyttsx3 from `sys.modules` so production import path raises."""
    saved = sys.modules.get("pyttsx3", "__MISSING__")
    sys.modules["pyttsx3"] = None
    try:
        yield
    finally:
        if saved == "__MISSING__":
            sys.modules.pop("pyttsx3", None)
        else:
            sys.modules["pyttsx3"] = saved


class TestSystemTTS:
    """Tests for SystemTTS class."""

    def test_name_property_returns_pyttsx3(self):
        # Arrange
        tts = _make_tts(_FakeEngine())
        # Act
        value = tts.name
        # Assert
        assert value == "pyttsx3"

    def test_default_rate_is_one_hundred_fifty(self):
        # Arrange
        tts = SystemTTS()
        # Act
        value = tts.rate
        # Assert
        assert value == 150

    def test_default_volume_is_one(self):
        # Arrange
        tts = SystemTTS()
        # Act
        value = tts.volume
        # Assert
        assert value == 1.0

    def test_default_voice_is_none(self):
        # Arrange
        tts = SystemTTS()
        # Act
        value = tts.voice
        # Assert
        assert value is None

    def test_custom_rate_initialization_preserves_rate(self):
        # Arrange
        # Act
        tts = SystemTTS(rate=200)
        # Assert
        assert tts.rate == 200

    def test_custom_volume_initialization_preserves_volume(self):
        # Arrange
        # Act
        tts = SystemTTS(volume=0.5)
        # Assert
        assert tts.volume == 0.5

    def test_custom_voice_initialization_preserves_voice(self):
        # Arrange
        # Act
        tts = SystemTTS(voice="en-us")
        # Assert
        assert tts.voice == "en-us"

    def test_engine_is_lazy_until_first_access(self):
        # Arrange
        # Act
        tts = SystemTTS()
        # Assert
        assert tts._engine is None

    def test_engine_property_sets_rate_on_engine(self):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        # Act
        _ = tts.engine
        # Assert
        assert fake.properties["rate"] == 150

    def test_engine_property_sets_volume_on_engine(self):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        # Act
        _ = tts.engine
        # Assert
        assert fake.properties["volume"] == 1.0

    def test_engine_property_returns_factory_built_engine(self):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        # Act
        engine = tts.engine
        # Assert
        assert engine is fake

    def test_engine_sets_voice_id_when_voice_matches_name(self):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English", id="en-us")])
        tts = _make_tts(fake, voice="English")
        # Act
        _ = tts.engine
        # Assert
        assert fake.properties["voice"] == "en-us"

    def test_missing_pyttsx3_module_raises_importerror_on_engine_access(
        self, no_pyttsx3
    ):
        # Arrange
        tts = SystemTTS()  # No engine_factory -> falls back to real import
        # Act
        ctx = pytest.raises((ImportError, TypeError))
        # Assert
        with ctx:
            _ = tts.engine

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(SystemTTS, BaseTTS)
        # Assert
        assert result is True

    def test_synthesize_records_save_to_file_invocation(self, tmp_path):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert fake.saved == [("Hello world", str(output_file))]

    def test_synthesize_runs_engine_after_save(self, tmp_path):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert fake.run_calls == 1

    def test_synthesize_returns_output_path_unchanged(self, tmp_path):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.synthesize("Hello world", str(output_file))
        # Assert
        assert result == output_file

    def test_synthesize_applies_voice_from_config(self, tmp_path):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English", id="en-us")])
        tts = _make_tts(fake)
        tts.config["voice"] = "English"
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Assert
        assert fake.properties["voice"] == "en-us"

    def test_speak_direct_passes_text_to_say(self):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        # Act
        tts.speak_direct("Hello world")
        # Assert
        assert fake.said == ["Hello world"]

    def test_speak_direct_runs_engine_after_say(self):
        # Arrange
        fake = _FakeEngine()
        tts = _make_tts(fake)
        # Act
        tts.speak_direct("Hello world")
        # Assert
        assert fake.run_calls == 1

    def test_speak_direct_applies_voice_from_config(self):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English", id="en-us")])
        tts = _make_tts(fake)
        tts.config["voice"] = "English"
        # Act
        tts.speak_direct("Hello")
        # Assert
        assert fake.properties["voice"] == "en-us"

    def test_get_voices_returns_two_voice_dicts(self):
        # Arrange
        fake = _FakeEngine(
            voices=[
                _FakeVoice(name="English", id="en-us", languages=["en"]),
                _FakeVoice(name="Spanish", id="es-es", languages=["es"]),
            ]
        )
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) == 2

    def test_get_voices_preserves_first_voice_name(self):
        # Arrange
        fake = _FakeEngine(
            voices=[
                _FakeVoice(name="English", id="en-us", languages=["en"]),
                _FakeVoice(name="Spanish", id="es-es", languages=["es"]),
            ]
        )
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["name"] == "English"

    def test_get_voices_preserves_first_voice_id(self):
        # Arrange
        fake = _FakeEngine(
            voices=[_FakeVoice(name="English", id="en-us", languages=["en"])]
        )
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["id"] == "en-us"

    def test_get_voices_tags_each_voice_as_system_type(self):
        # Arrange
        fake = _FakeEngine(
            voices=[_FakeVoice(name="English", id="en-us", languages=["en"])]
        )
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["type"] == "system"

    def test_get_voices_preserves_first_voice_languages(self):
        # Arrange
        fake = _FakeEngine(
            voices=[_FakeVoice(name="English", id="en-us", languages=["en"])]
        )
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["languages"] == ["en"]

    def test_get_voices_defaults_languages_to_empty_when_missing(self):
        # Arrange
        class _VoiceNoLanguages:
            name = "Test Voice"
            id = "test-id"

        fake = _FakeEngine(voices=[_VoiceNoLanguages()])
        tts = _make_tts(fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["languages"] == []

    def test_set_voice_matches_by_name_substring(self):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English Voice", id="en-voice-id")])
        tts = _make_tts(fake)
        # Act
        tts._set_voice("English")
        # Assert
        assert fake.properties["voice"] == "en-voice-id"

    def test_set_voice_matches_by_exact_id(self):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English Voice", id="en-voice-id")])
        tts = _make_tts(fake)
        # Act
        tts._set_voice("en-voice-id")
        # Assert
        assert fake.properties["voice"] == "en-voice-id"

    def test_set_voice_no_match_keeps_voice_unset(self):
        # Arrange
        fake = _FakeEngine(voices=[_FakeVoice(name="English Voice", id="en-voice-id")])
        tts = _make_tts(fake)
        _ = tts.engine  # trigger lazy init (sets rate, volume; not voice)
        # Act
        tts._set_voice("NonExistent Voice")
        # Assert
        assert "voice" not in fake.properties


class TestSystemTTSEdgeCases:
    """Edge case tests for SystemTTS."""

    def test_espeak_runtime_error_is_rewritten_with_install_hint(self):
        # Arrange
        def factory():
            raise RuntimeError("eSpeak not installed")

        tts = SystemTTS(engine_factory=factory)
        # Act
        ctx = pytest.raises(RuntimeError, match="espeak")
        # Assert
        with ctx:
            _ = tts.engine

    def test_other_runtime_error_propagates_unchanged(self):
        # Arrange
        def factory():
            raise RuntimeError("Some other error")

        tts = SystemTTS(engine_factory=factory)
        # Act
        ctx = pytest.raises(RuntimeError, match="Some other error")
        # Assert
        with ctx:
            _ = tts.engine

    def test_minimum_volume_zero_is_preserved(self):
        # Arrange
        # Act
        tts_min = SystemTTS(volume=0.0)
        # Assert
        assert tts_min.volume == 0.0

    def test_maximum_volume_one_is_preserved(self):
        # Arrange
        # Act
        tts_max = SystemTTS(volume=1.0)
        # Assert
        assert tts_max.volume == 1.0

    def test_high_rate_value_is_preserved(self):
        # Arrange
        # Act
        tts = SystemTTS(rate=500)
        # Assert
        assert tts.rate == 500

    def test_low_rate_value_is_preserved(self):
        # Arrange
        # Act
        tts = SystemTTS(rate=50)
        # Assert
        assert tts.rate == 50


class TestSystemTTSIntegration:
    """Integration tests for SystemTTS (require pyttsx3 installed)."""

    @pytest.mark.slow
    def test_real_engine_initialization_returns_non_none(self):
        # Arrange
        pytest.importorskip("pyttsx3")
        tts = SystemTTS()
        # Act
        try:
            engine = tts.engine
        except RuntimeError as e:
            if "espeak" in str(e).lower():
                pytest.skip("espeak not installed")
            raise
        # Assert
        assert engine is not None

    @pytest.mark.slow
    def test_real_get_voices_returns_list_type(self):
        # Arrange
        pytest.importorskip("pyttsx3")
        tts = SystemTTS()
        # Act
        try:
            voices = tts.get_voices()
        except RuntimeError as e:
            if "espeak" in str(e).lower():
                pytest.skip("espeak not installed")
            raise
        # Assert
        assert isinstance(voices, list)


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
