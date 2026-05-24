#!/usr/bin/env python3
# Timestamp: 2026-01-04
# File: tests/scitex_audio/_engines/test__pyttsx3_engine.py

"""Tests for scitex_audio._engines._pyttsx3_engine.

No mocks: the pyttsx3 engine is an injectable constructor seam
(``SystemTTS(engine=...)``). Tests pass a small hand-rolled fake engine that
records property/synthesis calls and serves fake voices. The lazy-init path
is exercised against the real ``pyttsx3`` module with ``importorskip``.
"""

import os

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._pyttsx3_engine import SystemTTS


class _FakeVoice:
    def __init__(self, name, voice_id, languages=None):
        self.name = name
        self.id = voice_id
        if languages is not None:
            self.languages = languages


class _FakeNoLangVoice:
    """Voice exposing only name + id (no ``languages`` attribute)."""

    def __init__(self, name, voice_id):
        self.name = name
        self.id = voice_id


class _FakePyttsx3Engine:
    """Records the pyttsx3 surface the engine actually drives."""

    def __init__(self, voices=None):
        self._voices = voices or []
        self.properties = {}
        self.set_property_calls = []
        self.saved = []
        self.said = []
        self.run_and_wait_count = 0

    def setProperty(self, key, value):
        self.properties[key] = value
        self.set_property_calls.append((key, value))

    def getProperty(self, key):
        if key == "voices":
            return self._voices
        return self.properties.get(key)

    def save_to_file(self, text, path):
        self.saved.append((text, path))

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        self.run_and_wait_count += 1


class TestSystemTTSDefaults:
    def test_name_is_pyttsx3(self):
        # Arrange
        tts = SystemTTS(engine=_FakePyttsx3Engine())
        # Act
        name = tts.name
        # Assert
        assert name == "pyttsx3"

    def test_default_rate_is_150(self):
        # Arrange
        # Act
        tts = SystemTTS()
        # Assert
        assert tts.rate == 150

    def test_default_volume_is_one(self):
        # Arrange
        # Act
        tts = SystemTTS()
        # Assert
        assert tts.volume == 1.0

    def test_default_voice_is_none(self):
        # Arrange
        # Act
        tts = SystemTTS()
        # Assert
        assert tts.voice is None

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(SystemTTS, BaseTTS)
        # Assert
        assert result is True


class TestSystemTTSInitialization:
    def test_custom_rate_stored(self):
        # Arrange
        # Act
        tts = SystemTTS(rate=200)
        # Assert
        assert tts.rate == 200

    def test_custom_volume_stored(self):
        # Arrange
        # Act
        tts = SystemTTS(volume=0.5)
        # Assert
        assert tts.volume == 0.5

    def test_custom_voice_stored(self):
        # Arrange
        # Act
        tts = SystemTTS(voice="en-us")
        # Assert
        assert tts.voice == "en-us"

    def test_engine_none_until_accessed(self):
        # Arrange
        # Act
        tts = SystemTTS()
        # Assert
        assert tts._engine is None

    def test_injected_engine_is_used(self):
        # Arrange
        fake = _FakePyttsx3Engine()
        # Act
        tts = SystemTTS(engine=fake)
        # Assert
        assert tts.engine is fake


@pytest.fixture
def real_pyttsx3_tts():
    """A SystemTTS whose lazy `engine` was initialized against real pyttsx3,
    or skip when no system TTS engine is available (e.g. headless CI)."""
    pytest.importorskip("pyttsx3")
    tts = SystemTTS(rate=175)
    try:
        tts.engine  # trigger lazy init
    except (RuntimeError, OSError):
        pytest.skip("no system TTS engine available on this host")
    return tts


class TestSystemTTSLazyInit:
    def test_real_engine_init_returns_an_engine(self, real_pyttsx3_tts):
        # Arrange
        # Act
        engine = real_pyttsx3_tts.engine
        # Assert
        assert engine is not None

    def test_real_engine_is_cached_across_access(self, real_pyttsx3_tts):
        # Arrange
        first = real_pyttsx3_tts.engine
        # Act
        second = real_pyttsx3_tts.engine
        # Assert
        assert first is second


class TestSystemTTSSynthesize:
    def test_save_to_file_receives_text_and_path(self, tmp_path):
        # Arrange
        fake = _FakePyttsx3Engine()
        tts = SystemTTS(engine=fake)
        output_file = tmp_path / "out.wav"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert fake.saved == [("Hello world", str(output_file))]

    def test_synthesize_runs_engine_once(self, tmp_path):
        # Arrange
        fake = _FakePyttsx3Engine()
        tts = SystemTTS(engine=fake)
        # Act
        tts.synthesize("Hello", str(tmp_path / "out.wav"))
        # Assert
        assert fake.run_and_wait_count == 1

    def test_synthesize_returns_output_path(self, tmp_path):
        # Arrange
        fake = _FakePyttsx3Engine()
        tts = SystemTTS(engine=fake)
        output_file = tmp_path / "out.wav"
        # Act
        result = tts.synthesize("Hello", str(output_file))
        # Assert
        assert result == output_file

    def test_synthesize_applies_voice_from_config(self, tmp_path):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English", "en-us")])
        tts = SystemTTS(engine=fake)
        tts.config["voice"] = "english"
        # Act
        tts.synthesize("Hello", str(tmp_path / "out.wav"))
        # Assert
        assert fake.properties.get("voice") == "en-us"


class TestSystemTTSSpeakDirect:
    def test_speak_direct_says_text(self):
        # Arrange
        fake = _FakePyttsx3Engine()
        tts = SystemTTS(engine=fake)
        # Act
        tts.speak_direct("Hello world")
        # Assert
        assert fake.said == ["Hello world"]

    def test_speak_direct_runs_engine_once(self):
        # Arrange
        fake = _FakePyttsx3Engine()
        tts = SystemTTS(engine=fake)
        # Act
        tts.speak_direct("Hello")
        # Assert
        assert fake.run_and_wait_count == 1

    def test_speak_direct_applies_voice_from_config(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English", "en-us")])
        tts = SystemTTS(engine=fake)
        tts.config["voice"] = "english"
        # Act
        tts.speak_direct("Hello")
        # Assert
        assert fake.properties.get("voice") == "en-us"


class TestSystemTTSGetVoices:
    def test_returns_one_dict_per_voice(self):
        # Arrange
        fake = _FakePyttsx3Engine(
            voices=[
                _FakeVoice("English", "en-us", ["en"]),
                _FakeVoice("Spanish", "es-es", ["es"]),
            ]
        )
        tts = SystemTTS(engine=fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) == 2

    def test_voice_dict_carries_name_id_type_languages(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English", "en-us", ["en"])])
        tts = SystemTTS(engine=fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0] == {
            "name": "English",
            "id": "en-us",
            "type": "system",
            "languages": ["en"],
        }

    def test_missing_languages_attr_defaults_to_empty(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeNoLangVoice("Test Voice", "test-id")])
        tts = SystemTTS(engine=fake)
        # Act
        voices = tts.get_voices()
        # Assert
        assert voices[0]["languages"] == []


class TestSystemTTSSetVoice:
    def test_set_voice_by_name_substring(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English Voice", "en-voice-id")])
        tts = SystemTTS(engine=fake)
        # Act
        tts._set_voice("english")
        # Assert
        assert fake.properties.get("voice") == "en-voice-id"

    def test_set_voice_by_exact_id(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English Voice", "en-voice-id")])
        tts = SystemTTS(engine=fake)
        # Act
        tts._set_voice("en-voice-id")
        # Assert
        assert fake.properties.get("voice") == "en-voice-id"

    def test_unknown_voice_keeps_default(self):
        # Arrange
        fake = _FakePyttsx3Engine(voices=[_FakeVoice("English", "en-us")])
        tts = SystemTTS(engine=fake)
        # Act
        tts._set_voice("nonexistent-language")
        # Assert
        assert "voice" not in fake.properties


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
