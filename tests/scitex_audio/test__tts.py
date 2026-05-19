#!/usr/bin/env python3
# Timestamp: "2026-03-14 (ywatanabe)"
# File: scitex-audio/tests/test__tts.py

"""Tests for scitex.audio._tts module (legacy ElevenLabs TTS)."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestTTSConfig:
    """Tests for TTSConfig dataclass."""

    def test_default_voice_id(self):
        """Test default voice ID is Adam (historical default: Rachel)."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Adam voice ID (the current default after the config refresh)
        # Assert
        assert config.voice_id == "pNInz6obpgDQGcFmaJgB"

    def test_default_voice_name_is_none(self):
        """Test default voice name is None."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.voice_name is None

    def test_default_model_id(self):
        """Test default model ID."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.model_id == "eleven_multilingual_v2"

    def test_default_stability_config_stability_equals_n_0_5(self):
        """Test default stability."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.stability == 0.5

    def test_default_similarity_boost(self):
        """Test default similarity_boost."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.similarity_boost == 0.75

    def test_default_style_config_style_equals_n_0_0(self):
        """Test default style."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.style == 0.0

    def test_default_speed_config_speed_equals_n_1_0(self):
        """Test default speed."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.speed == 1.0

    def test_default_output_format(self):
        """Test default output format."""
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig()
        # Assert
        assert config.output_format == "mp3_44100_128"

    def test_custom_values_config_voice_id_equals_custom_id(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.voice_id == "custom-id"

    def test_custom_values_config_voice_name_equals_custom(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.voice_name == "Custom"

    def test_custom_values_config_model_id_equals_custom_model(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.model_id == "custom_model"

    def test_custom_values_config_stability_equals_n_0_8(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.stability == 0.8

    def test_custom_values_config_similarity_boost_equals_n_0_9(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.similarity_boost == 0.9

    def test_custom_values_config_style_equals_n_0_5(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.style == 0.5

    def test_custom_values_config_speed_equals_n_1_5(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.speed == 1.5

    def test_custom_values_config_output_format_equals_wav_44100_16(self):
        # Arrange
        from scitex_audio._tts import TTSConfig

        # Act
        config = TTSConfig(
            voice_id="custom-id",
            voice_name="Custom",
            model_id="custom_model",
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            speed=1.5,
            output_format="wav_44100_16",
        )
        # Act
        # Assert
        assert config.output_format == "wav_44100_16"


class TestTTS:
    """Tests for TTS class."""

    def test_voices_dictionary_rachel_in_tts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._tts import TTS

        # Act
        # Assert
        assert "rachel" in TTS.VOICES

    def test_voices_dictionary_adam_in_tts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._tts import TTS

        # Act
        # Assert
        assert "adam" in TTS.VOICES

    def test_voices_dictionary_bella_in_tts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._tts import TTS

        # Act
        # Assert
        assert "bella" in TTS.VOICES

    def test_voices_dictionary_josh_in_tts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._tts import TTS

        # Act
        # Assert
        assert "josh" in TTS.VOICES

    def test_voices_dictionary_sam_in_tts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._tts import TTS

        # Act
        # Assert
        assert "sam" in TTS.VOICES

    def test_api_key_from_parameter(self):
        """Test API key from parameter."""
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS(api_key="test-api-key")
        # Assert
        assert tts.api_key == "test-api-key"

    def test_api_key_from_environment(self):
        """Test API key from environment variable."""
        # Arrange
        # Act
        # Assert
        env = {"ELEVENLABS_API_KEY": "env-api-key"}
        # Also clear the higher-priority env var so ELEVENLABS_API_KEY is used
        with patch.dict(os.environ, env):
            os.environ.pop("SCITEX_AUDIO_ELEVENLABS_API_KEY", None)
            from scitex_audio._tts import TTS

            tts = TTS()
            assert tts.api_key == "env-api-key"

    def test_voice_name_sets_voice_id(self):
        """Test voice_name parameter sets voice_id."""
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS(voice_name="rachel")
        # Assert
        assert tts.config.voice_id == TTS.VOICES["rachel"]

    def test_voice_id_overrides_voice_name(self):
        """Test voice_id parameter overrides voice_name."""
        # Arrange
        from scitex_audio._tts import TTS

        custom_id = "custom-voice-id"
        # Act
        tts = TTS(voice_name="rachel", voice_id=custom_id)
        # Assert
        assert tts.config.voice_id == custom_id

    def test_config_kwargs_passed_tts_config_stability_0_8(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Act
        # Assert
        assert tts.config.stability == 0.8

    def test_config_kwargs_passed_tts_config_speed_1_5(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS(stability=0.8, speed=1.5)
        # Act
        # Assert
        assert tts.config.speed == 1.5

    def test_client_lazy_loading(self):
        """Test client is lazily loaded."""
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Assert
        assert tts._client is None

    def test_client_import_error(self):
        """Test ImportError when elevenlabs not installed."""
        # Arrange
        from scitex_audio._tts import TTS

        tts = TTS()

        # Mock the internal import of elevenlabs to fail
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == "elevenlabs.client" or name.startswith("elevenlabs"):
                raise ImportError("elevenlabs not installed")
            return original_import(name, *args, **kwargs)

        # Act
        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(ImportError) as exc_info:
                _ = tts.client

        # Assert
        assert "elevenlabs" in str(exc_info.value)

    def test_speak_method_exists_hasattr_tts_speak(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Act
        # Assert
        assert hasattr(tts, "speak")

    def test_speak_method_exists_callable_tts_speak(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Act
        # Assert
        assert callable(tts.speak)

    def test_list_voices_method_exists_hasattr_tts_list_voices(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Act
        # Assert
        assert hasattr(tts, "list_voices")

    def test_list_voices_method_exists_callable_tts_list_voices(self):
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Act
        # Assert
        assert callable(tts.list_voices)

    def test_speak_with_mocked_client_result_equals_output_file(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        # Act
        with patch.object(tts, "_play_audio"):
            result = tts.speak("Hello", output_path=str(output_file), play=False)
        # Act
        # Assert
        assert result == output_file

    def test_speak_with_mocked_client_output_file_exists(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        # Act
        with patch.object(tts, "_play_audio"):
            result = tts.speak("Hello", output_path=str(output_file), play=False)
        # Act
        # Assert
        assert output_file.exists()

    def test_speak_uses_custom_voice_name(self, tmp_path):
        """Test speak uses voice_name parameter."""
        # Arrange
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client

        output_file = tmp_path / "test.mp3"

        with patch.object(tts, "_play_audio"):
            tts.speak(
                "Hello", output_path=str(output_file), voice_name="adam", play=False
            )

        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Assert
        assert call_kwargs["voice_id"] == TTS.VOICES["adam"]

    def test_speak_uses_custom_voice_id(self, tmp_path):
        """Test speak uses voice_id parameter."""
        # Arrange
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client

        output_file = tmp_path / "test.mp3"
        custom_id = "custom-voice-id"

        with patch.object(tts, "_play_audio"):
            tts.speak(
                "Hello", output_path=str(output_file), voice_id=custom_id, play=False
            )

        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Assert
        assert call_kwargs["voice_id"] == custom_id

    def test_speak_plays_audio_by_default(self, tmp_path):
        """Test speak plays audio by default."""
        # Arrange
        # Act
        # Assert
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client

        with patch.object(tts, "_play_audio") as mock_play:
            tts.speak("Hello")
            mock_play.assert_called_once()
            assert mock_play.call_count == 1

    def test_speak_returns_none_without_output_path(self, tmp_path):
        """Test speak returns None when no output_path specified."""
        # Arrange
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client

        # Act
        with patch.object(tts, "_play_audio"):
            result = tts.speak("Hello", play=True)

        # Assert
        assert result is None

    def test_list_voices_returns_list_voices_is_list(self):
        # Arrange
        mock_client = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "Test Voice"
        mock_voice.voice_id = "test-id"
        mock_voice.labels = {}
        mock_response = MagicMock()
        mock_response.voices = [mock_voice]
        mock_client.voices.get_all.return_value = mock_response
        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client
        # Act
        voices = tts.list_voices()
        # Act
        # Assert
        assert isinstance(voices, list)

    def test_list_voices_returns_list_len_voices_is_1(self):
        # Arrange
        mock_client = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "Test Voice"
        mock_voice.voice_id = "test-id"
        mock_voice.labels = {}
        mock_response = MagicMock()
        mock_response.voices = [mock_voice]
        mock_client.voices.get_all.return_value = mock_response
        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client
        # Act
        voices = tts.list_voices()
        # Act
        # Assert
        assert len(voices) == 1

    def test_list_voices_returns_list_voices_0_name_test_voice(self):
        # Arrange
        mock_client = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "Test Voice"
        mock_voice.voice_id = "test-id"
        mock_voice.labels = {}
        mock_response = MagicMock()
        mock_response.voices = [mock_voice]
        mock_client.voices.get_all.return_value = mock_response
        from scitex_audio._tts import TTS

        tts = TTS(api_key="test-key")
        tts._client = mock_client
        # Act
        voices = tts.list_voices()
        # Act
        # Assert
        assert voices[0]["name"] == "Test Voice"


class TestTTSPlayAudio:
    """Tests for TTS audio playback methods."""

    def test_play_audio_tries_multiple_players(self, tmp_path):
        """Test _play_audio tries multiple players."""
        # Arrange
        # Act
        # Assert
        from scitex_audio._tts import TTS

        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("player not found")
            # Should not raise
            tts._play_audio(test_file)
            assert mock_run.called

    def test_play_audio_windows_fallback(self, tmp_path):
        """Test Windows fallback is tried in WSL."""
        # Arrange
        # Act
        # Assert
        from scitex_audio._tts import TTS

        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")

        with patch("os.path.exists", return_value=True):  # Simulate WSL
            with patch.object(
                tts, "_play_audio_windows", return_value=True
            ) as mock_win:
                tts._play_audio(test_file)
                mock_win.assert_called_once()
                assert mock_win.call_count == 1

    def test_play_audio_windows_returns_false_non_wsl(self, tmp_path):
        """Test _play_audio_windows returns False when not in WSL."""
        # Arrange
        # Act
        # Assert
        from scitex_audio._tts import TTS

        tts = TTS()
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"dummy")

        with patch("os.path.exists", return_value=False):
            result = tts._play_audio_windows(test_file)
            assert result is False


class TestModuleLevelSpeak:
    """Tests for module-level speak function."""

    def test_speak_function_exists(self):
        """Test speak function exists at module level."""
        # Arrange
        # Act
        from scitex_audio._tts import speak

        # Assert
        assert callable(speak)

    def test_speak_creates_default_tts(self):
        """Test speak creates default TTS instance."""
        # Arrange
        # Act
        # Assert
        from scitex_audio import _tts

        # Reset the default TTS
        _tts._default_tts = None

        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        with patch.object(
            _tts.TTS, "client", new_callable=lambda: property(lambda s: mock_client)
        ):
            with patch.object(_tts.TTS, "_play_audio"):
                _tts.speak("Hello", play=False)

        # Should have created a default TTS
        assert _tts._default_tts is not None

    def test_speak_with_voice_parameter_voice_in_sig_parameters(self):
        # Arrange
        import inspect
        from scitex_audio._tts import speak

        # Act
        sig = inspect.signature(speak)
        # Act
        # Assert
        assert "voice" in sig.parameters

    def test_speak_with_voice_parameter_play_in_sig_parameters(self):
        # Arrange
        import inspect
        from scitex_audio._tts import speak

        # Act
        sig = inspect.signature(speak)
        # Act
        # Assert
        assert "play" in sig.parameters

    def test_speak_with_voice_parameter_output_path_in_sig_parameters(self):
        # Arrange
        import inspect
        from scitex_audio._tts import speak

        # Act
        sig = inspect.signature(speak)
        # Act
        # Assert
        assert "output_path" in sig.parameters


class TestTTSEdgeCases:
    """Edge case tests for TTS."""

    def test_empty_text_tts_is_not_none(self):
        """Test handling of empty text."""
        # Arrange
        from scitex_audio._tts import TTS

        # Act
        tts = TTS()
        # Should not raise during initialization
        # Assert
        assert tts is not None

    def test_voice_name_case_insensitive(self):
        """Test voice_name is case insensitive."""
        # Arrange
        from scitex_audio._tts import TTS

        tts_lower = TTS(voice_name="rachel")
        tts_upper = TTS(voice_name="RACHEL")
        # Act
        tts_mixed = TTS(voice_name="Rachel")

        # Assert
        assert (
            tts_lower.config.voice_id
            == tts_upper.config.voice_id
            == tts_mixed.config.voice_id
        )


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# EOF
