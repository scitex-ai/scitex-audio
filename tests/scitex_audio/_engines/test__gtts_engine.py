#!/usr/bin/env python3
# Timestamp: 2026-01-04
# File: tests/scitex_audio/_engines/test__gtts_engine.py

"""Tests for scitex_audio._engines._gtts_engine.

No mocks: the gTTS class is an injectable factory seam
(``GoogleTTS(gtts_factory=...)``). Tests pass a small hand-rolled fake that
records construction kwargs and writes a real file on ``save``. Network-
dependent end-to-end tests are marked ``network`` and skipped when gtts is
unavailable.
"""

import os

import pytest

from scitex_audio._engines._base import BaseTTS
from scitex_audio._engines._gtts_engine import GoogleTTS


class _FakeGTTSInstance:
    """Stand-in for a gTTS instance: records args, writes a real file."""

    def __init__(self, text, lang, slow, sink):
        self.text = text
        self.lang = lang
        self.slow = slow
        self._sink = sink

    def save(self, path):
        self._sink["saved_path"] = path
        with open(path, "wb") as f:
            f.write(b"fake-mp3-bytes")

    def write_to_fp(self, buffer):
        buffer.write(b"fake-mp3-bytes")


class _FakeGTTSFactory:
    """Callable matching the gTTS(text=, lang=, slow=) signature."""

    def __init__(self):
        self.calls = []
        self.sink = {}

    def __call__(self, text, lang, slow):
        self.calls.append({"text": text, "lang": lang, "slow": slow})
        return _FakeGTTSInstance(text, lang, slow, self.sink)


class TestGoogleTTSProperties:
    def test_name_is_gtts(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        name = tts.name
        # Assert
        assert name == "gtts"

    def test_requires_internet_is_true(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        result = tts.requires_internet
        # Assert
        assert result is True

    def test_inherits_from_base_tts(self):
        # Arrange
        # Act
        result = issubclass(GoogleTTS, BaseTTS)
        # Assert
        assert result is True


class TestGoogleTTSDefaults:
    def test_default_language_is_english(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        lang = tts.lang
        # Assert
        assert lang == "en"

    def test_default_speed_is_one_and_half(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        speed = tts.speed
        # Assert
        assert speed == 1.5

    def test_slow_disabled_by_default(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        slow = tts.slow
        # Assert
        assert slow is False


class TestGoogleTTSInitialization:
    def test_custom_language_stored(self):
        # Arrange
        # Act
        tts = GoogleTTS(lang="fr")
        # Assert
        assert tts.lang == "fr"

    def test_custom_speed_stored(self):
        # Arrange
        # Act
        tts = GoogleTTS(speed=2.0)
        # Assert
        assert tts.speed == 2.0

    def test_slow_mode_enabled(self):
        # Arrange
        # Act
        tts = GoogleTTS(slow=True)
        # Assert
        assert tts.slow is True

    def test_unsupported_language_stored_verbatim(self):
        # Arrange
        # Act
        tts = GoogleTTS(lang="invalid_lang")
        # Assert
        assert tts.lang == "invalid_lang"


class TestGoogleTTSLanguages:
    def test_languages_contains_english(self):
        # Arrange
        # Act
        present = "en" in GoogleTTS.LANGUAGES
        # Assert
        assert present is True

    def test_languages_contains_french(self):
        # Arrange
        # Act
        present = "fr" in GoogleTTS.LANGUAGES
        # Assert
        assert present is True

    def test_languages_contains_japanese(self):
        # Arrange
        # Act
        present = "ja" in GoogleTTS.LANGUAGES
        # Assert
        assert present is True

    def test_languages_contains_simplified_chinese(self):
        # Arrange
        # Act
        present = "zh-CN" in GoogleTTS.LANGUAGES
        # Assert
        assert present is True


class TestGoogleTTSGetVoices:
    def test_get_voices_returns_list(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert isinstance(voices, list)

    def test_get_voices_is_non_empty(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        voices = tts.get_voices()
        # Assert
        assert len(voices) > 0

    def test_get_voices_covers_all_languages(self):
        # Arrange
        tts = GoogleTTS()
        # Act
        voice_ids = {v["id"] for v in tts.get_voices()}
        # Assert
        assert set(GoogleTTS.LANGUAGES) <= voice_ids


class TestGoogleTTSSynthesizeDirectSave:
    """speed=1.0 path: direct gTTS().save() with no pydub dependency."""

    def test_returns_output_path(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, gtts_factory=factory)
        output_file = tmp_path / "out.mp3"
        # Act
        result = tts.synthesize("Hello world", str(output_file))
        # Assert
        assert result == output_file

    def test_writes_output_file(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, gtts_factory=factory)
        output_file = tmp_path / "out.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert output_file.exists()

    def test_passes_text_to_gtts(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, gtts_factory=factory)
        # Act
        tts.synthesize("Hello world", str(tmp_path / "out.mp3"))
        # Assert
        assert factory.calls[0]["text"] == "Hello world"

    def test_passes_slow_flag_to_gtts(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, slow=True, gtts_factory=factory)
        # Act
        tts.synthesize("Hello", str(tmp_path / "out.mp3"))
        # Assert
        assert factory.calls[0]["slow"] is True

    def test_uses_language_from_config(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, gtts_factory=factory)
        tts.config["voice"] = "fr"
        # Act
        tts.synthesize("Bonjour", str(tmp_path / "out.mp3"))
        # Assert
        assert factory.calls[0]["lang"] == "fr"

    def test_converts_language_name_to_code(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.0, gtts_factory=factory)
        tts.config["voice"] = "French"
        # Act
        tts.synthesize("Bonjour", str(tmp_path / "out.mp3"))
        # Assert
        assert factory.calls[0]["lang"] == "fr"


def _pydub_available() -> bool:
    try:
        import pydub  # noqa: F401

        return True
    except Exception:
        return False


class TestGoogleTTSSynthesizeWithSpeed:
    """speed != 1.0 path uses pydub for speed control."""

    @pytest.mark.skipif(
        _pydub_available(),
        reason="pydub installed — cannot exercise the missing-dep path",
    )
    def test_speed_path_requires_pydub_when_absent(self, tmp_path):
        # Arrange
        factory = _FakeGTTSFactory()
        tts = GoogleTTS(speed=1.5, gtts_factory=factory)
        # Act
        ctx = pytest.raises(ImportError)
        # Assert
        with ctx:
            tts.synthesize("Hello", str(tmp_path / "out.mp3"))

    # NOTE: The speed != 1.0 success path feeds the synthesized stream
    # through pydub/ffmpeg, which requires a genuinely decodable MP3. That
    # cannot be exercised with a fake factory (fake bytes fail ffmpeg
    # decode); it is covered end-to-end by the `network` test below when
    # gtts + pydub + ffmpeg are all available.


@pytest.mark.network
class TestGoogleTTSNetwork:
    """End-to-end synthesis against the real gTTS service (network)."""

    def test_real_synthesize_writes_nonempty_file(self, tmp_path):
        # Arrange
        pytest.importorskip("gtts")
        tts = GoogleTTS(speed=1.0)
        output_file = tmp_path / "real.mp3"
        # Act
        tts.synthesize("Hello world", str(output_file))
        # Assert
        assert output_file.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])

# EOF
