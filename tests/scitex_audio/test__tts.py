#!/usr/bin/env python3
# Timestamp: "2026-05-23 (proj-scitex-audio)"
# File: scitex-audio/tests/scitex_audio/test__tts.py

"""Tests for scitex_audio._tts (legacy ElevenLabs TTS facade).

Mock-free rewrite. The TTS class already exposes its `_client`
attribute, so tests inject a hand-rolled `_FakeElevenLabsClient` that
records every `text_to_speech.convert(...)` call. Playback is
exercised through a `_play_audio` refactor that accepts injected
`runner` / `is_wsl` keyword parameters — no mock.patch on
`subprocess.run` or `os.path.exists`.

Env-var coverage uses a yield-based `env_save_restore` fixture; the
"elevenlabs not installed" path uses a `no_elevenlabs_client` fixture
that sets `sys.modules["elevenlabs.client"] = None` so the production
import path raises naturally.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import scitex_audio._tts as _tts_mod
from scitex_audio._tts import TTS, TTSConfig, speak

_API_KEY_ENV_VARS = (
    "ELEVENLABS_API_KEY",
    "SCITEX_AUDIO_ELEVENLABS_API_KEY",
)


class _FakeConvertResult:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def __iter__(self):
        return iter(self._chunks)


class _FakeTextToSpeech:
    def __init__(self, chunks):
        self.calls: list[dict] = []
        self._chunks = chunks

    def convert(self, **kwargs):
        self.calls.append(dict(kwargs))
        return _FakeConvertResult(self._chunks)


class _FakeVoiceResponse:
    def __init__(self, voices):
        self.voices = voices


class _FakeVoices:
    def __init__(self, voices=None):
        self._voices = voices or []

    def get_all(self):
        return _FakeVoiceResponse(self._voices)


class _FakeElevenLabsClient:
    def __init__(self, *, chunks=None, voices=None):
        self.text_to_speech = _FakeTextToSpeech(chunks or [b"audio"])
        self.voices = _FakeVoices(voices=voices)


class _FakeRemoteVoice:
    def __init__(self, name: str, voice_id: str, labels: dict[str, Any]):
        self.name = name
        self.voice_id = voice_id
        self.labels = labels


@pytest.fixture
def env_save_restore():
    """Snapshot the two ElevenLabs API-key env vars; restore on teardown."""
    saved = {k: os.environ.get(k) for k in _API_KEY_ENV_VARS}
    for k in _API_KEY_ENV_VARS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@pytest.fixture
def no_elevenlabs_client():
    """Hide `elevenlabs.client` so the lazy import raises."""
    saved = sys.modules.get("elevenlabs.client", "__MISSING__")
    sys.modules["elevenlabs.client"] = None
    try:
        yield
    finally:
        if saved == "__MISSING__":
            sys.modules.pop("elevenlabs.client", None)
        else:
            sys.modules["elevenlabs.client"] = saved


def _with_fake_client(tts: TTS, client: _FakeElevenLabsClient) -> TTS:
    tts._client = client
    return tts


def _silent_play_audio(self, path, *, runner=None, is_wsl=None, timeout=30):
    """No-op replacement that satisfies the production speak() flow."""
    return None


class TestTTSConfig:
    """Tests for TTSConfig dataclass."""

    def test_default_voice_id_is_adam(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.voice_id == "pNInz6obpgDQGcFmaJgB"

    def test_default_voice_name_is_none(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.voice_name is None

    def test_default_model_id_is_multilingual_v2(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.model_id == "eleven_multilingual_v2"

    def test_default_stability_is_half(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.stability == 0.5

    def test_default_similarity_boost_is_three_quarters(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.similarity_boost == 0.75

    def test_default_style_is_zero(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.style == 0.0

    def test_default_speed_is_one(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.speed == 1.0

    def test_default_output_format_is_mp3_44100_128(self):
        # Arrange
        # Act
        config = TTSConfig()
        # Assert
        assert config.output_format == "mp3_44100_128"

    def test_custom_voice_id_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(voice_id="custom-id")
        # Assert
        assert config.voice_id == "custom-id"

    def test_custom_voice_name_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(voice_name="Custom")
        # Assert
        assert config.voice_name == "Custom"

    def test_custom_model_id_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(model_id="custom_model")
        # Assert
        assert config.model_id == "custom_model"

    def test_custom_stability_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(stability=0.8)
        # Assert
        assert config.stability == 0.8

    def test_custom_similarity_boost_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(similarity_boost=0.9)
        # Assert
        assert config.similarity_boost == 0.9

    def test_custom_style_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(style=0.5)
        # Assert
        assert config.style == 0.5

    def test_custom_speed_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(speed=1.5)
        # Assert
        assert config.speed == 1.5

    def test_custom_output_format_is_preserved(self):
        # Arrange
        # Act
        config = TTSConfig(output_format="wav_44100_16")
        # Assert
        assert config.output_format == "wav_44100_16"


class TestTTS:
    """Tests for TTS class."""

    def test_voices_table_contains_rachel_preset(self):
        # Arrange
        # Act
        keys = TTS.VOICES
        # Assert
        assert "rachel" in keys

    def test_voices_table_contains_adam_preset(self):
        # Arrange
        # Act
        keys = TTS.VOICES
        # Assert
        assert "adam" in keys

    def test_voices_table_contains_bella_preset(self):
        # Arrange
        # Act
        keys = TTS.VOICES
        # Assert
        assert "bella" in keys

    def test_voices_table_contains_josh_preset(self):
        # Arrange
        # Act
        keys = TTS.VOICES
        # Assert
        assert "josh" in keys

    def test_voices_table_contains_sam_preset(self):
        # Arrange
        # Act
        keys = TTS.VOICES
        # Assert
        assert "sam" in keys

    def test_api_key_from_parameter_is_preserved(self):
        # Arrange
        # Act
        tts = TTS(api_key="test-api-key")
        # Assert
        assert tts.api_key == "test-api-key"

    def test_api_key_read_from_elevenlabs_env_var(self, env_save_restore):
        # Arrange
        os.environ["ELEVENLABS_API_KEY"] = "env-api-key"
        # Act
        tts = TTS()
        # Assert
        assert tts.api_key == "env-api-key"

    def test_voice_name_resolves_to_preset_voice_id(self):
        # Arrange
        # Act
        tts = TTS(voice_name="rachel")
        # Assert
        assert tts.config.voice_id == TTS.VOICES["rachel"]

    def test_voice_id_kwarg_overrides_voice_name(self):
        # Arrange
        custom_id = "custom-voice-id"
        # Act
        tts = TTS(voice_name="rachel", voice_id=custom_id)
        # Assert
        assert tts.config.voice_id == custom_id

    def test_config_stability_kwarg_passes_through(self):
        # Arrange
        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Assert
        assert tts.config.stability == 0.8

    def test_config_speed_kwarg_passes_through(self):
        # Arrange
        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Assert
        assert tts.config.speed == 1.5

    def test_client_is_lazy_until_first_access(self):
        # Arrange
        # Act
        tts = TTS()
        # Assert
        assert tts._client is None

    def test_client_property_raises_importerror_without_elevenlabs(
        self, no_elevenlabs_client
    ):
        # Arrange
        tts = TTS()
        # Act
        ctx = pytest.raises(ImportError, match="elevenlabs")
        # Assert
        with ctx:
            _ = tts.client

    def test_tts_exposes_callable_speak_method(self):
        # Arrange
        tts = TTS()
        # Act
        value = callable(tts.speak)
        # Assert
        assert value is True

    def test_tts_exposes_callable_list_voices_method(self):
        # Arrange
        tts = TTS()
        # Act
        value = callable(tts.list_voices)
        # Assert
        assert value is True

    def test_speak_with_fake_client_returns_supplied_output_path(self, tmp_path):
        # Arrange
        tts = _with_fake_client(
            TTS(api_key="test-key"),
            _FakeElevenLabsClient(chunks=[b"audio", b"data"]),
        )
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert result == output_file

    def test_speak_with_fake_client_writes_output_file_to_disk(self, tmp_path):
        # Arrange
        tts = _with_fake_client(
            TTS(api_key="test-key"),
            _FakeElevenLabsClient(chunks=[b"audio", b"data"]),
        )
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak("Hello", output_path=str(output_file), play=False)
        # Assert
        assert output_file.exists()

    def test_speak_threads_voice_name_into_resolved_voice_id(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio"])
        tts = _with_fake_client(TTS(api_key="test-key"), client)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.speak(
            "Hello", output_path=str(output_file), voice_name="adam", play=False
        )
        # Assert
        assert client.text_to_speech.calls[0]["voice_id"] == TTS.VOICES["adam"]

    def test_speak_threads_explicit_voice_id_into_convert_call(self, tmp_path):
        # Arrange
        client = _FakeElevenLabsClient(chunks=[b"audio"])
        tts = _with_fake_client(TTS(api_key="test-key"), client)
        output_file = tmp_path / "test.mp3"
        custom_id = "custom-voice-id"
        # Act
        tts.speak(
            "Hello", output_path=str(output_file), voice_id=custom_id, play=False
        )
        # Assert
        assert client.text_to_speech.calls[0]["voice_id"] == custom_id

    def test_speak_default_play_true_invokes_play_audio_once(self, monkeypatch_free):
        # See note on monkeypatch_free below for why we lift this fixture.
        # Arrange
        tts = _with_fake_client(
            TTS(api_key="test-key"),
            _FakeElevenLabsClient(chunks=[b"audio"]),
        )
        recorded: list[Path] = []

        def _record_play(self, path, *, runner=None, is_wsl=None, timeout=30):
            recorded.append(path)

        monkeypatch_free.swap_method(TTS, "_play_audio", _record_play)
        # Act
        tts.speak("Hello")
        # Assert
        assert len(recorded) == 1

    def test_speak_returns_none_when_no_output_path_supplied(self, monkeypatch_free):
        # Arrange
        tts = _with_fake_client(
            TTS(api_key="test-key"),
            _FakeElevenLabsClient(chunks=[b"audio"]),
        )
        monkeypatch_free.swap_method(TTS, "_play_audio", _silent_play_audio)
        # Act
        result = tts.speak("Hello", play=True)
        # Assert
        assert result is None

    def test_list_voices_returns_list_type(self):
        # Arrange
        client = _FakeElevenLabsClient(
            voices=[_FakeRemoteVoice(name="Test Voice", voice_id="test-id", labels={})]
        )
        tts = _with_fake_client(TTS(api_key="test-key"), client)
        # Act
        voices = tts.list_voices()
        # Assert
        assert isinstance(voices, list)

    def test_list_voices_returns_single_entry_for_single_remote_voice(self):
        # Arrange
        client = _FakeElevenLabsClient(
            voices=[_FakeRemoteVoice(name="Test Voice", voice_id="test-id", labels={})]
        )
        tts = _with_fake_client(TTS(api_key="test-key"), client)
        # Act
        voices = tts.list_voices()
        # Assert
        assert len(voices) == 1

    def test_list_voices_preserves_voice_name_in_output(self):
        # Arrange
        client = _FakeElevenLabsClient(
            voices=[_FakeRemoteVoice(name="Test Voice", voice_id="test-id", labels={})]
        )
        tts = _with_fake_client(TTS(api_key="test-key"), client)
        # Act
        voices = tts.list_voices()
        # Assert
        assert voices[0]["name"] == "Test Voice"


class TestTTSPlayAudio:
    """Tests for TTS audio playback methods."""

    def test_play_audio_invokes_injected_runner(self, tmp_path):
        # Arrange
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        calls: list[list[str]] = []

        def fake_runner(cmd, **kwargs):
            calls.append(cmd)
            # Pretend the first player succeeds — production stops trying.
            return subprocess.CompletedProcess(cmd, 0)

        # Act
        tts._play_audio(test_file, runner=fake_runner, is_wsl=False)
        # Assert
        assert len(calls) == 1

    def test_play_audio_falls_back_after_filenotfound(self, tmp_path):
        # Arrange
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        calls: list[list[str]] = []

        def fake_runner(cmd, **kwargs):
            calls.append(cmd)
            raise FileNotFoundError("no player")

        # Act
        tts._play_audio(test_file, runner=fake_runner, is_wsl=False)
        # Assert
        assert len(calls) == 4  # tries every player

    def test_play_audio_wsl_uses_windows_fallback_when_successful(self, tmp_path):
        # Arrange — subclass overrides _play_audio_windows to record + succeed.
        class _RecordingTTS(TTS):
            wsl_calls: list[Path] = []

            def _play_audio_windows(self, path: Path) -> bool:
                _RecordingTTS.wsl_calls.append(path)
                return True

        tts = _RecordingTTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        # Act
        tts._play_audio(test_file, runner=lambda *_a, **_k: None, is_wsl=True)
        # Assert
        assert len(_RecordingTTS.wsl_calls) == 1

    @pytest.mark.skipif(
        os.path.exists("/mnt/c/Windows"),
        reason="WSL host present — non-WSL branch can't be reached",
    )
    def test_play_audio_windows_returns_false_on_non_wsl_host(self, tmp_path):
        # Arrange — real non-WSL host: production short-circuits on path check.
        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")
        # Act
        result = tts._play_audio_windows(test_file)
        # Assert
        assert result is False


class TestModuleLevelSpeak:
    """Tests for module-level speak function."""

    def test_module_level_speak_is_callable(self):
        # Arrange
        # Act
        value = callable(speak)
        # Assert
        assert value is True

    def test_module_level_speak_creates_default_tts(self, monkeypatch_free):
        # Arrange — reset singleton, install a recording TTS subclass that
        # avoids the real network + playback paths.
        _tts_mod._default_tts = None

        class _RecordingDefaultTTS(TTS):
            def speak(self, *args, **kwargs):
                return None

        monkeypatch_free.swap_module_attr(_tts_mod, "TTS", _RecordingDefaultTTS)
        # Act
        speak("Hello", play=False)
        # Assert
        assert _tts_mod._default_tts is not None

    def test_speak_signature_exposes_voice_parameter(self):
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(speak)
        # Assert
        assert "voice" in sig.parameters

    def test_speak_signature_exposes_play_parameter(self):
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(speak)
        # Assert
        assert "play" in sig.parameters

    def test_speak_signature_exposes_output_path_parameter(self):
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(speak)
        # Assert
        assert "output_path" in sig.parameters


class TestTTSEdgeCases:
    """Edge case tests for TTS."""

    def test_construction_with_no_args_returns_non_none(self):
        # Arrange
        # Act
        tts = TTS()
        # Assert
        assert tts is not None

    def test_voice_name_resolution_is_case_insensitive(self):
        # Arrange
        tts_lower = TTS(voice_name="rachel")
        tts_upper = TTS(voice_name="RACHEL")
        # Act
        match = tts_lower.config.voice_id == tts_upper.config.voice_id
        # Assert
        assert match is True


# -- swap helper fixture (no-mocks alternative to pytest's monkeypatch) -------


class _SwapHelper:
    """Records swaps and reverses them on teardown — no monkeypatch."""

    def __init__(self) -> None:
        self._undo = []

    def swap_method(self, cls, name, new):
        original = cls.__dict__.get(name, "__NOT_SET__")
        setattr(cls, name, new)
        self._undo.append(lambda: _restore_cls(cls, name, original))

    def swap_module_attr(self, mod, name, new):
        original = getattr(mod, name, "__NOT_SET__")
        setattr(mod, name, new)
        self._undo.append(lambda: _restore_mod(mod, name, original))

    def teardown(self):
        for fn in reversed(self._undo):
            fn()
        self._undo.clear()


def _restore_cls(cls, name, original):
    if original == "__NOT_SET__":
        try:
            delattr(cls, name)
        except AttributeError:
            pass
    else:
        setattr(cls, name, original)


def _restore_mod(mod, name, original):
    if original == "__NOT_SET__":
        try:
            delattr(mod, name)
        except AttributeError:
            pass
    else:
        setattr(mod, name, original)


@pytest.fixture
def monkeypatch_free():
    helper = _SwapHelper()
    try:
        yield helper
    finally:
        helper.teardown()


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
