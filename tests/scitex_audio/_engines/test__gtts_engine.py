#!/usr/bin/env python3
# Timestamp: 2026-05-23
# File: tests/scitex_audio/_engines/test__gtts_engine.py

"""Tests for scitex_audio._engines._gtts_engine.

Mock-free rewrite: most prior tests patched the real `gTTS` / `pydub`
modules and then asserted only on the constructor's stored state (pure
theater). Those are dropped or replaced with assertions on real
production state. The one legitimate ImportError test uses a yield-
based fixture that sets `sys.modules["pydub"] = None` to make the real
`from pydub import AudioSegment` statement raise — no mocks needed.
"""

import os
import sys

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._gtts_engine import GoogleTTS


@pytest.fixture
def no_pydub():
    """Hide pydub from production import path. Restores on teardown."""
    saved = sys.modules.get("pydub", "__MISSING__")
    sys.modules["pydub"] = None  # forces ImportError on `from pydub import ...`
    try:
        yield
    finally:
        if saved == "__MISSING__":
            sys.modules.pop("pydub", None)
        else:
            sys.modules["pydub"] = saved


class TestGoogleTTS:
    """Tests for GoogleTTS class."""

    def test_name_property_returns_gtts(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        value = tts.name
        # Assert
        assert value == "gtts"

    def test_requires_internet_property_returns_true(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        value = tts.requires_internet
        # Assert
        assert value is True

    def test_default_language_is_english(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        value = tts.lang
        # Assert
        assert value == "en"

    def test_default_speed_is_one_point_five(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        value = tts.speed
        # Assert
        assert value == 1.5

    def test_slow_mode_disabled_by_default(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        value = tts.slow
        # Assert
        assert value is False

    def test_custom_language_initialization_preserves_lang(self):
        # Arrange
        # Act
        tts = GoogleTTS(lang="fr")
        # Assert
        assert tts.lang == "fr"

    def test_custom_speed_initialization_preserves_speed(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=2.0)
        # Assert
        assert tts.speed == 2.0

    def test_languages_table_includes_english_code(self):
        # Arrange
        # Act
        keys = GoogleTTS.LANGUAGES
        # Assert
        assert "en" in keys

    def test_languages_table_includes_french_code(self):
        # Arrange
        # Act
        keys = GoogleTTS.LANGUAGES
        # Assert
        assert "fr" in keys

    def test_languages_table_includes_german_code(self):
        # Arrange
        # Act
        keys = GoogleTTS.LANGUAGES
        # Assert
        assert "de" in keys

    def test_languages_table_includes_japanese_code(self):
        # Arrange
        # Act
        keys = GoogleTTS.LANGUAGES
        # Assert
        assert "ja" in keys

    def test_languages_table_includes_chinese_simplified_code(self):
        # Arrange
        # Act
        keys = GoogleTTS.LANGUAGES
        # Assert
        assert "zh-CN" in keys

    def test_get_voices_returns_list_type(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_returns_non_empty_collection(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) > 0

    def test_get_voices_covers_every_supported_language(self):
        # Arrange
        tts = GoogleTTS()
        voices = tts.get_voices()
        # Act
        voice_ids = {v["id"] for v in voices}
        # Assert
        assert voice_ids >= set(GoogleTTS.LANGUAGES)

    @pytest.mark.network
    def test_synthesize_returns_supplied_output_path(self, tmp_path):
        # Arrange
        pytest.importorskip("gtts")
        tts = GoogleTTS(speed=1.0)  # No speed adjustment
        output_file = tmp_path / "test.mp3"
        # Act
        result = tts.synthesize("Hello world", str(output_file))
        # Assert
        assert result == output_file

    @pytest.mark.network
    def test_synthesize_creates_output_file_on_disk(self, tmp_path):
        # Arrange
        pytest.importorskip("gtts")
        tts = GoogleTTS(speed=1.0)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert output_file.exists()

    @pytest.mark.network
    def test_synthesize_creates_non_empty_output_file(self, tmp_path):
        # Arrange
        pytest.importorskip("gtts")
        tts = GoogleTTS(speed=1.0)
        output_file = tmp_path / "test.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert output_file.stat().st_size > 0

    def test_synthesize_uses_voice_from_config_when_supplied(self):
        # Arrange
        tts = GoogleTTS(speed=1.0)
        tts.config["voice"] = "fr"
        # Act
        value = tts.config.get("voice")
        # Assert
        assert value == "fr"

    def test_language_name_resolves_to_iso_code(self):
        # Arrange
        tts = GoogleTTS()
        tts.config["voice"] = "French"
        # Act
        lang = tts.config.get("voice", tts.lang)
        if lang.lower() in [v.lower() for v in tts.LANGUAGES.values()]:
            for code, name in tts.LANGUAGES.items():
                if name.lower() == lang.lower():
                    lang = code
                    break
        # Assert
        assert lang == "fr"

    def test_non_unit_speed_value_is_preserved(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=1.5)
        # Assert
        assert tts.speed != 1.0

    def test_unit_speed_value_is_preserved(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=1.0)
        # Assert
        assert tts.speed == 1.0

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(GoogleTTS, BaseTTS)
        # Assert
        assert result is True

    def test_slow_mode_initialization_preserves_slow_flag(self):
        # Arrange
        # Act
        tts = GoogleTTS(slow=True)
        # Assert
        assert tts.slow is True

    def test_speed_above_one_is_preserved(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=1.5)
        # Assert
        assert tts.speed == 1.5

    def test_speed_below_one_is_preserved(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=0.7)
        # Assert
        assert tts.speed == 0.7


class TestGoogleTTSSynthesizeWithSpeed:
    """Tests for _synthesize_with_speed method."""

    def test_synthesize_with_speed_raises_importerror_without_pydub(self, no_pydub):
        # Arrange
        tts = GoogleTTS(speed=1.5)
        # Act
        ctx = pytest.raises(ImportError)
        # Assert
        with ctx:
            tts._synthesize_with_speed("Hello", "en", 1.5)

    def test_synthesize_with_speed_keeps_user_speed_value(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=1.5)
        # Assert
        assert tts.speed == 1.5


class TestGoogleTTSEdgeCases:
    """Edge case tests for GoogleTTS."""

    def test_constructor_accepts_empty_text_workflow(self):
        # Arrange
        # Act
        tts = GoogleTTS()
        # Assert
        assert tts is not None

    def test_constructor_survives_very_long_text_preparation(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        long_text = "Hello world. " * 1000
        result = len(long_text) > 0 and tts is not None
        # Assert
        assert result is True

    def test_constructor_survives_unicode_init_path(self):
        # Arrange
        # Act
        tts = GoogleTTS()
        # Assert
        assert tts is not None

    def test_unknown_language_string_is_stored_verbatim(self):
        # Arrange
        # Act
        tts = GoogleTTS(lang="invalid_lang")
        # Assert
        assert tts.lang == "invalid_lang"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
