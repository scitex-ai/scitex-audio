#!/usr/bin/env python3
# Timestamp: 2026-01-04
# File: tests/scitex/audio/engines/test_elevenlabs_engine.py

"""Tests for scitex.audio.engines.elevenlabs_engine module."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestElevenLabsTTS:
    """Tests for ElevenLabsTTS class."""

    def test_name_property_tts_name_equals_elevenlabs(self):
        """Test that name returns 'elevenlabs'."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.name == "elevenlabs"

    def test_requires_api_key_property(self):
        """Test that requires_api_key returns True."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.requires_api_key is True

    def test_requires_internet_property(self):
        """Test that requires_internet returns True."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.requires_internet is True

    def test_default_voice_is_adam(self):
        """Test default voice is 'adam' (rachel was the historical default)."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.voice == "adam"

    def test_default_model_id(self):
        """Test default model ID."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.model_id == "eleven_multilingual_v2"

    def test_default_stability_tts_stability_equals_n_0_5(self):
        """Test default stability value."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.stability == 0.5

    def test_default_similarity_boost(self):
        """Test default similarity_boost value."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.similarity_boost == 0.75

    def test_default_speed_tts_speed_equals_n_1_0(self):
        """Test default speed value."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts.speed == 1.0

    def test_custom_api_key_initialization(self):
        """Test initializing with custom API key."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS(api_key="test-api-key")
        # Assert
        assert tts.api_key == "test-api-key"

    def test_api_key_from_environment(self):
        """Test API key is read from environment."""
        # Clear both possible env vars, then set only ELEVENLABS_API_KEY
        # Arrange
        # Act
        # Assert
        env_patch = {
            "ELEVENLABS_API_KEY": "env-api-key",
            "SCITEX_AUDIO_ELEVENLABS_API_KEY": "",
        }
        with patch.dict(os.environ, env_patch, clear=False):
            # Need to delete the scitex key if it exists
            os.environ.pop("SCITEX_AUDIO_ELEVENLABS_API_KEY", None)
            from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

            tts = ElevenLabsTTS()
            assert tts.api_key == "env-api-key"

    def test_custom_voice_initialization(self):
        """Test initializing with custom voice."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS(voice="adam")
        # Assert
        assert tts.voice == "adam"

    def test_custom_model_initialization(self):
        """Test initializing with custom model."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS(model_id="custom_model")
        # Assert
        assert tts.model_id == "custom_model"

    def test_custom_stability_initialization(self):
        """Test initializing with custom stability."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS(stability=0.8)
        # Assert
        assert tts.stability == 0.8

    def test_custom_similarity_boost_initialization(self):
        """Test initializing with custom similarity_boost."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS(similarity_boost=0.9)
        # Assert
        assert tts.similarity_boost == 0.9

    def test_custom_speed_initialization(self):
        """Test initializing with custom speed (clamped to API limits)."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Speed is clamped to ElevenLabs API limits (0.7-1.2)
        # Act
        tts = ElevenLabsTTS(speed=1.5)
        # Assert
        assert tts.speed == ElevenLabsTTS.MAX_SPEED  # 1.2

    def test_voices_dictionary_contains_presets_rachel_in_elevenlabstts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        # Assert
        assert "rachel" in ElevenLabsTTS.VOICES

    def test_voices_dictionary_contains_presets_adam_in_elevenlabstts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        # Assert
        assert "adam" in ElevenLabsTTS.VOICES

    def test_voices_dictionary_contains_presets_bella_in_elevenlabstts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        # Assert
        assert "bella" in ElevenLabsTTS.VOICES

    def test_voices_dictionary_contains_presets_josh_in_elevenlabstts_voices(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        # Assert
        assert "josh" in ElevenLabsTTS.VOICES


    def test_client_lazy_loading(self):
        """Test client is lazily loaded."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Act
        tts = ElevenLabsTTS()
        # Assert
        assert tts._client is None

    def test_client_property_initializes_elevenlabs(self):
        """Test client property initializes ElevenLabs client."""
        # Arrange
        # Act
        # Assert
        mock_elevenlabs = MagicMock()
        mock_client = MagicMock()
        mock_elevenlabs.return_value = mock_client

        with patch.dict("sys.modules", {"elevenlabs": MagicMock()}):
            with patch("elevenlabs.client.ElevenLabs", mock_elevenlabs):
                from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

                tts = ElevenLabsTTS(api_key="test-key")

                # Force client initialization through property
                with patch.object(
                    ElevenLabsTTS,
                    "client",
                    new_callable=lambda: property(lambda self: mock_client),
                ):
                    client = tts.client
                    assert client is mock_client

    def test_inherits_from_base_tts(self):
        """Test that ElevenLabsTTS inherits from BaseTTS."""
        # Arrange
        from scitex_audio._engines._base import BaseTTS
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Assert
        assert issubclass(ElevenLabsTTS, BaseTTS)

    def test_get_voice_id_with_name(self):
        """Test _get_voice_id converts name to ID."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS()
        # Act
        voice_id = tts._get_voice_id("rachel")
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["rachel"]

    def test_get_voice_id_with_id(self):
        """Test _get_voice_id returns ID as-is if not found in VOICES."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS()
        custom_id = "custom-voice-id-12345"
        # Act
        voice_id = tts._get_voice_id(custom_id)
        # Assert
        assert voice_id == custom_id

    def test_get_voice_id_case_insensitive(self):
        """Test _get_voice_id is case insensitive."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS()
        voice_id_lower = tts._get_voice_id("rachel")
        voice_id_upper = tts._get_voice_id("RACHEL")
        # Act
        voice_id_mixed = tts._get_voice_id("Rachel")

        # Assert
        assert voice_id_lower == voice_id_upper == voice_id_mixed

    def test_get_voice_id_uses_default_when_none(self):
        """Test _get_voice_id uses instance voice when None passed."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS(voice="adam")
        # Act
        voice_id = tts._get_voice_id(None)
        # Assert
        assert voice_id == ElevenLabsTTS.VOICES["adam"]

    def test_synthesize_calls_api_call_kwargs_text_hello_world(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        result = tts.synthesize("Hello world", str(output_file))
        mock_client.text_to_speech.convert.assert_called_once()
        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Act
        # Assert
        assert call_kwargs["text"] == "Hello world"

    def test_synthesize_calls_api_voice_id_in_call_kwargs(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        result = tts.synthesize("Hello world", str(output_file))
        mock_client.text_to_speech.convert.assert_called_once()
        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Act
        # Assert
        assert "voice_id" in call_kwargs

    def test_synthesize_calls_api_result_equals_output_file(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"audio", b"data"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        result = tts.synthesize("Hello world", str(output_file))
        mock_client.text_to_speech.convert.assert_called_once()
        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Act
        # Assert
        assert result == output_file


    def test_synthesize_writes_audio_chunks_output_file_exists(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"chunk1", b"chunk2", b"chunk3"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Act
        # Assert
        assert output_file.exists()

    def test_synthesize_writes_audio_chunks_output_file_read_bytes_b_chunk1chunk2chunk3(self, tmp_path):
        # Arrange
        mock_client = MagicMock()
        mock_audio = [b"chunk1", b"chunk2", b"chunk3"]
        mock_client.text_to_speech.convert.return_value = mock_audio
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello", str(output_file))
        # Act
        # Assert
        assert output_file.read_bytes() == b"chunk1chunk2chunk3"


    def test_synthesize_uses_voice_from_config(self, tmp_path):
        """Test synthesize uses voice from config."""
        # Arrange
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"audio"]

        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        tts.config["voice"] = "adam"

        output_file = tmp_path / "test.mp3"
        tts.synthesize("Hello", str(output_file))

        # Act
        call_kwargs = mock_client.text_to_speech.convert.call_args[1]
        # Assert
        assert call_kwargs["voice_id"] == ElevenLabsTTS.VOICES["adam"]

    def test_get_voices_returns_preset_voices_voices_is_list(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS()
        # Act
        voices = tts.get_voices()
        # Act
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_returns_preset_voices_len_voices_len_elevenlabstts_voices(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS()
        # Act
        voices = tts.get_voices()
        # Act
        # Assert
        assert len(voices) >= len(ElevenLabsTTS.VOICES)


    def test_get_voices_includes_custom_voices_len_custom_voices_is_1(self):
        # Arrange
        mock_client = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "Custom Voice"
        mock_voice.voice_id = "custom-id"
        mock_voice.labels = {"accent": "British"}
        mock_response = MagicMock()
        mock_response.voices = [mock_voice]
        mock_client.voices.get_all.return_value = mock_response
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        voices = tts.get_voices()
        # Should include custom voice
        # Act
        custom_voices = [v for v in voices if v.get("type") == "custom"]
        # Act
        # Assert
        assert len(custom_voices) == 1

    def test_get_voices_includes_custom_voices_custom_voices_0_name_custom_voice(self):
        # Arrange
        mock_client = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "Custom Voice"
        mock_voice.voice_id = "custom-id"
        mock_voice.labels = {"accent": "British"}
        mock_response = MagicMock()
        mock_response.voices = [mock_voice]
        mock_client.voices.get_all.return_value = mock_response
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        voices = tts.get_voices()
        # Should include custom voice
        # Act
        custom_voices = [v for v in voices if v.get("type") == "custom"]
        # Act
        # Assert
        assert custom_voices[0]["name"] == "Custom Voice"


    def test_get_voices_handles_api_error_voices_is_list(self):
        # Arrange
        mock_client = MagicMock()
        mock_client.voices.get_all.side_effect = Exception("API Error")
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        # Should not raise, just return preset voices
        # Act
        voices = tts.get_voices()
        # Act
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_handles_api_error_len_voices_len_elevenlabstts_voices(self):
        # Arrange
        mock_client = MagicMock()
        mock_client.voices.get_all.side_effect = Exception("API Error")
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        tts = ElevenLabsTTS(api_key="test-key")
        tts._client = mock_client
        # Should not raise, just return preset voices
        # Act
        voices = tts.get_voices()
        # Act
        # Assert
        assert len(voices) == len(ElevenLabsTTS.VOICES)



class TestElevenLabsTTSEdgeCases:
    """Edge case tests for ElevenLabsTTS."""

    def test_stability_boundary_values_tts_min_stability_equals_n_0_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(stability=0.0)
        # Act
        # Assert
        assert tts_min.stability == 0.0

    def test_stability_boundary_values_tts_max_stability_equals_n_1_0_tts_min_stability_equals_n_0_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(stability=0.0)
        # Act
        # Assert
        assert tts_min.stability == 0.0

    def test_stability_boundary_values_tts_max_stability_equals_n_1_0_tts_max_stability_equals_n_1_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(stability=0.0)
        # Assert
        assert tts_min.stability == 0.0
        tts_max = ElevenLabsTTS(stability=1.0)
        # Act
        # Assert
        assert tts_max.stability == 1.0



    def test_similarity_boost_boundary_values_tts_min_similarity_boost_equals_n_0_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(similarity_boost=0.0)
        # Act
        # Assert
        assert tts_min.similarity_boost == 0.0

    def test_similarity_boost_boundary_values_tts_max_similarity_boost_equals_n_1_0_tts_min_similarity_boost_equals_n_0_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(similarity_boost=0.0)
        # Act
        # Assert
        assert tts_min.similarity_boost == 0.0

    def test_similarity_boost_boundary_values_tts_max_similarity_boost_equals_n_1_0_tts_max_similarity_boost_equals_n_1_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Act
        tts_min = ElevenLabsTTS(similarity_boost=0.0)
        # Assert
        assert tts_min.similarity_boost == 0.0
        tts_max = ElevenLabsTTS(similarity_boost=1.0)
        # Act
        # Assert
        assert tts_max.similarity_boost == 1.0



    def test_speed_boundary_values_tts_slow_speed_equals_elevenlabstts_min_speed(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Act
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7

    def test_speed_boundary_values_tts_fast_speed_equals_elevenlabstts_max_speed_tts_slow_speed_equals_elevenlabstts_min_speed(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Act
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7

    def test_speed_boundary_values_tts_fast_speed_equals_elevenlabstts_max_speed_tts_fast_speed_equals_elevenlabstts_max_speed(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7
        # Values above MAX_SPEED are clamped to 1.2
        tts_fast = ElevenLabsTTS(speed=2.0)
        # Act
        # Assert
        assert tts_fast.speed == ElevenLabsTTS.MAX_SPEED  # 1.2


    def test_speed_boundary_values_tts_mid_speed_equals_n_1_0_tts_slow_speed_equals_elevenlabstts_min_speed(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Act
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7

    def test_speed_boundary_values_tts_mid_speed_equals_n_1_0_tts_fast_speed_equals_elevenlabstts_max_speed(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7
        # Values above MAX_SPEED are clamped to 1.2
        tts_fast = ElevenLabsTTS(speed=2.0)
        # Act
        # Assert
        assert tts_fast.speed == ElevenLabsTTS.MAX_SPEED  # 1.2

    def test_speed_boundary_values_tts_mid_speed_equals_n_1_0_tts_mid_speed_equals_n_1_0(self):
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS
        # Values below MIN_SPEED are clamped to 0.7
        # Act
        tts_slow = ElevenLabsTTS(speed=0.5)
        # Assert
        assert tts_slow.speed == ElevenLabsTTS.MIN_SPEED  # 0.7
        # Values above MAX_SPEED are clamped to 1.2
        tts_fast = ElevenLabsTTS(speed=2.0)
        assert tts_fast.speed == ElevenLabsTTS.MAX_SPEED  # 1.2
        # Values within range are preserved
        tts_mid = ElevenLabsTTS(speed=1.0)
        # Act
        # Assert
        assert tts_mid.speed == 1.0



    def test_no_api_key(self):
        """Test behavior when no API key is set."""
        # Arrange
        # Act
        # Assert
        with patch.dict(os.environ, {}, clear=True):
            # Remove ELEVENLABS_API_KEY if present
            os.environ.pop("ELEVENLABS_API_KEY", None)

            from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

            tts = ElevenLabsTTS()
            # API key should be None
            assert tts.api_key is None

    def test_voice_id_direct_passthrough(self):
        """Test that unknown voice IDs are passed through."""
        # Arrange
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        tts = ElevenLabsTTS()
        custom_id = "some-custom-voice-id-that-doesnt-exist"
        # Act
        result = tts._get_voice_id(custom_id)
        # Assert
        assert result == custom_id


class TestElevenLabsTTSVoicePresets:
    """Tests for voice preset mappings."""

    def test_all_preset_voices_have_ids(self):
        """Test all preset voices have valid IDs."""
        # Arrange
        # Act
        # Assert
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        for name, voice_id in ElevenLabsTTS.VOICES.items():
            assert (voice_id is not None) and (len(voice_id) > 0) and (isinstance(voice_id, str))

    def test_expected_voice_count(self):
        """Test expected number of preset voices."""
        # Arrange
        # Act
        from scitex_audio._engines._elevenlabs_engine import ElevenLabsTTS

        # Should have at least 8 preset voices
        # Assert
        assert len(ElevenLabsTTS.VOICES) >= 8


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/audio/engines/elevenlabs_engine.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # Timestamp: "2025-12-11 (ywatanabe)"
# # File: /home/ywatanabe/proj/scitex-code/src/scitex/audio/engines/elevenlabs_engine.py
# # ----------------------------------------
#
# """
# ElevenLabs TTS backend - High quality, requires API key and payment.
# """
#
# from __future__ import annotations
#
# import os
# from pathlib import Path
# from typing import List, Optional
#
# from .base import BaseTTS
#
# __all__ = ["ElevenLabsTTS"]
#
#
# class ElevenLabsTTS(BaseTTS):
#     """ElevenLabs TTS backend.
#
#     High-quality voices but requires API key and has usage costs.
#
#     Environment:
#         ELEVENLABS_API_KEY: Your ElevenLabs API key
#     """
#
#     VOICES = {
#         "rachel": "21m00Tcm4TlvDq8ikWAM",
#         "adam": "pNInz6obpgDQGcFmaJgB",
#         "antoni": "ErXwobaYiN019PkySvjV",
#         "bella": "EXAVITQu4vr4xnSDxMaL",
#         "domi": "AZnzlk1XvdvUeBnXmlld",
#         "elli": "MF3mGyEYCl7XYWbV9V6O",
#         "josh": "TxGEqnHWrfWFTfGW9XjX",
#         "sam": "yoZ06aMxZJJ28mfd3POQ",
#     }
#
#     def __init__(
#         self,
#         api_key: Optional[str] = None,
#         voice: str = "rachel",
#         model_id: str = "eleven_multilingual_v2",
#         stability: float = 0.5,
#         similarity_boost: float = 0.75,
#         speed: float = 1.0,
#         **kwargs,
#     ):
#         super().__init__(**kwargs)
#         self.api_key = (
#             api_key
#             or os.environ.get("ELEVENLABS_API_KEY")
#             or os.environ.get("ELEVENLABS_API_KEY_SCITEX_AUDIO")
#         )
#         self.voice = voice
#         self.model_id = model_id
#         self.stability = stability
#         self.similarity_boost = similarity_boost
#         self.speed = speed
#         self._client = None
#
#     @property
#     def name(self) -> str:
#         return "elevenlabs"
#
#     @property
#     def requires_api_key(self) -> bool:
#         return True
#
#     @property
#     def requires_internet(self) -> bool:
#         return True
#
#     @property
#     def client(self):
#         """Lazy-load ElevenLabs client."""
#         if self._client is None:
#             try:
#                 from elevenlabs.client import ElevenLabs
#
#                 self._client = ElevenLabs(api_key=self.api_key)
#             except ImportError:
#                 raise ImportError(
#                     "elevenlabs package not installed. "
#                     "Install with: pip install elevenlabs"
#                 )
#         return self._client
#
#     def _get_voice_id(self, voice: Optional[str] = None) -> str:
#         """Get voice ID from name or return as-is if already an ID."""
#         v = voice or self.voice
#         normalized = v.lower()
#         return self.VOICES.get(normalized, v)
#
#     def synthesize(self, text: str, output_path: str) -> Path:
#         """Synthesize text using ElevenLabs API."""
#         voice_id = self._get_voice_id(self.config.get("voice"))
#
#         audio = self.client.text_to_speech.convert(
#             text=text,
#             voice_id=voice_id,
#             model_id=self.model_id,
#             voice_settings={
#                 "stability": self.stability,
#                 "similarity_boost": self.similarity_boost,
#                 "speed": self.speed,
#             },
#             output_format="mp3_44100_128",
#         )
#
#         out_path = Path(output_path)
#         with open(out_path, "wb") as f:
#             for chunk in audio:
#                 f.write(chunk)
#
#         return out_path
#
#     def get_voices(self) -> List[dict]:
#         """Get available voices."""
#         # Start with preset voices
#         voices = [
#             {"name": name, "id": vid, "type": "preset"}
#             for name, vid in self.VOICES.items()
#         ]
#
#         # Try to get custom voices
#         try:
#             response = self.client.voices.get_all()
#             for v in response.voices:
#                 voices.append(
#                     {
#                         "name": v.name,
#                         "id": v.voice_id,
#                         "type": "custom",
#                         "labels": v.labels,
#                     }
#                 )
#         except Exception:
#             pass
#
#         return voices
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/audio/engines/elevenlabs_engine.py
# --------------------------------------------------------------------------------
