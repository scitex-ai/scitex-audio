#!/usr/bin/env python3
"""Tests for scitex_audio._mcp.handlers (MCP server tool handlers).

Covers:
  - generate_audio_handler  (mocked tts_speak)
  - list_backends_handler   (mocked available_backends)
  - list_voices_handler     (mocked get_tts.get_voices)
  - play_audio_handler      (file-not-found path; happy path with mocked play)
  - list_audio_files_handler (tmpdir scan)
  - clear_audio_cache_handler (tmpdir, max_age_hours semantics)
  - check_audio_status_handler (mocked check_wsl_audio)
  - speech_queue_status_handler (smoke; lock-state agnostic)
  - announce_context_handler (mocked subprocess + speak_handler)
  - speak_handler            (cloud-relay path AND local path)
  - _emit_browser_speech     (OSC escape semantics)
  - _get_signature           (smoke)

The cloud-relay test cluster is preserved here (previously in
test_handlers_cloud_relay.py) so all handlers.py coverage lives in one
mirror file (audit-project §2 PS204).
"""

import asyncio
import base64
import io
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_osc_text(stderr_output: str) -> str:
    """Extract and base64-decode the text carried in an OSC 9999 escape."""
    prefix = "\x1b]9999;speak:"
    suffix = "\x07"
    assert prefix in stderr_output, f"OSC prefix not found in: {stderr_output!r}"
    start = stderr_output.index(prefix) + len(prefix)
    end = stderr_output.index(suffix, start)
    b64 = stderr_output[start:end]
    return base64.b64decode(b64.encode()).decode()


def _run(coro):
    """Run a coroutine synchronously without disturbing the running loop."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# generate_audio_handler
# ---------------------------------------------------------------------------


class TestGenerateAudioHandler:
    def test_returns_path_and_size_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # tts_speak is imported lazily inside the handler; patch the module attr.
        def fake_speak(**kwargs):
            return out_file
        monkeypatch.setattr("scitex_audio.speak", fake_speak, raising=False)
        # Act
        result = _run(
            handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Act
        # Assert
        assert result["success"] is True

    def test_returns_path_and_size_result_path_str_out_file(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # tts_speak is imported lazily inside the handler; patch the module attr.
        def fake_speak(**kwargs):
            return out_file
        monkeypatch.setattr("scitex_audio.speak", fake_speak, raising=False)
        # Act
        result = _run(
            handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Act
        # Assert
        assert result["path"] == str(out_file)

    def test_returns_path_and_size_result_text_hello(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # tts_speak is imported lazily inside the handler; patch the module attr.
        def fake_speak(**kwargs):
            return out_file
        monkeypatch.setattr("scitex_audio.speak", fake_speak, raising=False)
        # Act
        result = _run(
            handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Act
        # Assert
        assert result["text"] == "hello"

    def test_returns_path_and_size_result_size_kb_0(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # tts_speak is imported lazily inside the handler; patch the module attr.
        def fake_speak(**kwargs):
            return out_file
        monkeypatch.setattr("scitex_audio.speak", fake_speak, raising=False)
        # Act
        result = _run(
            handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Act
        # Assert
        assert result["size_kb"] >= 0


    def test_failure_returns_error_result_success_is_false(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        def boom(**kwargs):
            raise RuntimeError("boom")
        monkeypatch.setattr("scitex_audio.speak", boom, raising=False)
        # Act
        result = _run(handlers.generate_audio_handler(text="hi"))
        # Act
        # Assert
        assert result["success"] is False

    def test_failure_returns_error_boom_in_result_error(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        def boom(**kwargs):
            raise RuntimeError("boom")
        monkeypatch.setattr("scitex_audio.speak", boom, raising=False)
        # Act
        result = _run(handlers.generate_audio_handler(text="hi"))
        # Act
        # Assert
        assert "boom" in result["error"]



# ---------------------------------------------------------------------------
# list_backends_handler
# ---------------------------------------------------------------------------


class TestListBackendsHandler:
    def test_reports_available_and_default_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_reports_available_and_default_result_available_gtts(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["available"] == ["gtts"]

    def test_reports_available_and_default_result_default_gtts(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["default"] == "gtts"  # first available in FALLBACK_ORDER

    def test_reports_available_and_default_gtts_in_names_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_reports_available_and_default_gtts_in_names_result_available_gtts(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["available"] == ["gtts"]

    def test_reports_available_and_default_gtts_in_names_result_default_gtts(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["default"] == "gtts"  # first available in FALLBACK_ORDER

    def test_reports_available_and_default_gtts_in_names_gtts_in_names(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Assert
        assert (result['success'] is True) and (result['available'] == ['gtts']) and (result['default'] == 'gtts')
        names = {b["name"] for b in result["backends"]}
        # Act
        # Assert
        assert "gtts" in names



    def test_no_backends_default_is_none_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: [], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_no_backends_default_is_none_result_default_is_none(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: [], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["gtts", "pyttsx3"],
            raising=False,
        )
        # Act
        result = _run(handlers.list_backends_handler())
        # Act
        # Assert
        assert result["default"] is None



# ---------------------------------------------------------------------------
# list_voices_handler
# ---------------------------------------------------------------------------


class TestListVoicesHandler:
    def test_returns_voices_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_tts = MagicMock()
        fake_tts.get_voices.return_value = ["en", "fr", "ja"]
        monkeypatch.setattr(
            "scitex_audio.get_tts", lambda backend: fake_tts, raising=False
        )
        # Act
        result = _run(handlers.list_voices_handler(backend="gtts"))
        # Act
        # Assert
        assert result["success"] is True

    def test_returns_voices_result_count_3(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_tts = MagicMock()
        fake_tts.get_voices.return_value = ["en", "fr", "ja"]
        monkeypatch.setattr(
            "scitex_audio.get_tts", lambda backend: fake_tts, raising=False
        )
        # Act
        result = _run(handlers.list_voices_handler(backend="gtts"))
        # Act
        # Assert
        assert result["count"] == 3

    def test_returns_voices_result_backend_gtts(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_tts = MagicMock()
        fake_tts.get_voices.return_value = ["en", "fr", "ja"]
        monkeypatch.setattr(
            "scitex_audio.get_tts", lambda backend: fake_tts, raising=False
        )
        # Act
        result = _run(handlers.list_voices_handler(backend="gtts"))
        # Act
        # Assert
        assert result["backend"] == "gtts"


    def test_failure_returns_error_result_success_is_false(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        def boom(backend):
            raise ValueError("no such backend")
        monkeypatch.setattr("scitex_audio.get_tts", boom, raising=False)
        # Act
        result = _run(handlers.list_voices_handler(backend="nope"))
        # Act
        # Assert
        assert result["success"] is False

    def test_failure_returns_error_no_such_backend_in_result_error(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        def boom(backend):
            raise ValueError("no such backend")
        monkeypatch.setattr("scitex_audio.get_tts", boom, raising=False)
        # Act
        result = _run(handlers.list_voices_handler(backend="nope"))
        # Act
        # Assert
        assert "no such backend" in result["error"]



# ---------------------------------------------------------------------------
# play_audio_handler
# ---------------------------------------------------------------------------


class TestPlayAudioHandler:
    def test_missing_file_returns_error_result_success_is_false(self):
        # Arrange
        from scitex_audio._mcp import handlers
        # Act
        result = _run(handlers.play_audio_handler(path="/no/such/file.wav"))
        # Act
        # Assert
        assert result["success"] is False

    def test_missing_file_returns_error_not_found_in_result_error_lower(self):
        # Arrange
        from scitex_audio._mcp import handlers
        # Act
        result = _run(handlers.play_audio_handler(path="/no/such/file.wav"))
        # Act
        # Assert
        assert "not found" in result["error"].lower()


    def test_existing_file_invokes_play_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        # _play_audio is a method of BaseTTS; bypass real audio call.
        from scitex_audio._engines._base import BaseTTS
        monkeypatch.setattr(BaseTTS, "_play_audio", lambda self, p: None, raising=False)
        # Act
        result = _run(handlers.play_audio_handler(path=str(f)))
        # Act
        # Assert
        assert result["success"] is True

    def test_existing_file_invokes_play_result_played_str_f(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        # _play_audio is a method of BaseTTS; bypass real audio call.
        from scitex_audio._engines._base import BaseTTS
        monkeypatch.setattr(BaseTTS, "_play_audio", lambda self, p: None, raising=False)
        # Act
        result = _run(handlers.play_audio_handler(path=str(f)))
        # Act
        # Assert
        assert result["played"] == str(f)



# ---------------------------------------------------------------------------
# list_audio_files_handler
# ---------------------------------------------------------------------------


class TestListAudioFilesHandler:
    def test_lists_files_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=10))
        # Act
        # Assert
        assert result["success"] is True

    def test_lists_files_result_count_2(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=10))
        # Act
        # Assert
        assert result["count"] == 2

    def test_lists_files_names_equals_a_mp3_b_wav_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=10))
        # Act
        # Assert
        assert result["success"] is True

    def test_lists_files_names_equals_a_mp3_b_wav_result_count_2(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=10))
        # Act
        # Assert
        assert result["count"] == 2

    def test_lists_files_names_equals_a_mp3_b_wav_names_equals_a_mp3_b_wav(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=10))
        # Assert
        assert (result['success'] is True) and (result['count'] == 2)
        names = {f["name"] for f in result["files"]}
        # Act
        # Assert
        assert names == {"a.mp3", "b.wav"}



    def test_limit_respected_result_count_2(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        for i in range(5):
            (audio_dir / f"f{i}.mp3").write_bytes(b"x")

        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.list_audio_files_handler(limit=2))
        # Assert
        assert result["count"] == 2


# ---------------------------------------------------------------------------
# clear_audio_cache_handler
# ---------------------------------------------------------------------------


class TestClearAudioCacheHandler:
    def test_clears_all_when_max_age_zero_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=0))
        # Act
        # Assert
        assert result["success"] is True

    def test_clears_all_when_max_age_zero_result_deleted_2(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=0))
        # Act
        # Assert
        assert result["deleted"] == 2

    def test_clears_all_when_max_age_zero_not_list_audio_dir_glob_mp3(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=0))
        # Act
        # Assert
        assert not list(audio_dir.glob("*.mp3"))


    def test_keeps_fresh_files_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        # File is fresh (just created), so 24h cutoff should keep it.
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert result["success"] is True

    def test_keeps_fresh_files_result_deleted_0(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        # File is fresh (just created), so 24h cutoff should keep it.
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert result["deleted"] == 0

    def test_keeps_fresh_files_f_exists(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        # File is fresh (just created), so 24h cutoff should keep it.
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert f.exists()


    def test_deletes_stale_files_result_success_is_true(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        # Backdate mtime to 48h ago.
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert result["success"] is True

    def test_deletes_stale_files_result_deleted_1(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        # Backdate mtime to 48h ago.
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert result["deleted"] == 1

    def test_deletes_stale_files_not_f_exists(self, tmp_path, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        # Backdate mtime to 48h ago.
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        # Act
        # Assert
        assert not f.exists()



# ---------------------------------------------------------------------------
# check_audio_status_handler
# ---------------------------------------------------------------------------


class TestCheckAudioStatusHandler:
    def test_wraps_check_wsl_audio_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_status = {"is_wsl": True, "recommended": "linux"}
        monkeypatch.setattr(
            "scitex_audio.check_wsl_audio", lambda: dict(fake_status), raising=False
        )
        # Act
        result = _run(handlers.check_audio_status_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_wraps_check_wsl_audio_result_is_wsl_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_status = {"is_wsl": True, "recommended": "linux"}
        monkeypatch.setattr(
            "scitex_audio.check_wsl_audio", lambda: dict(fake_status), raising=False
        )
        # Act
        result = _run(handlers.check_audio_status_handler())
        # Act
        # Assert
        assert result["is_wsl"] is True

    def test_wraps_check_wsl_audio_timestamp_in_result(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_status = {"is_wsl": True, "recommended": "linux"}
        monkeypatch.setattr(
            "scitex_audio.check_wsl_audio", lambda: dict(fake_status), raising=False
        )
        # Act
        result = _run(handlers.check_audio_status_handler())
        # Act
        # Assert
        assert "timestamp" in result



# ---------------------------------------------------------------------------
# speech_queue_status_handler
# ---------------------------------------------------------------------------


class TestSpeechQueueStatusHandler:
    def test_returns_success_envelope_result_success_is_true(self):
        # Arrange
        from scitex_audio._mcp import handlers
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_returns_success_envelope_locked_in_result(self):
        # Arrange
        from scitex_audio._mcp import handlers
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Act
        # Assert
        assert "locked" in result

    def test_returns_success_envelope_message_in_result(self):
        # Arrange
        from scitex_audio._mcp import handlers
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Act
        # Assert
        assert "message" in result



# ---------------------------------------------------------------------------
# announce_context_handler
# ---------------------------------------------------------------------------


class TestAnnounceContextHandler:
    def test_speaks_directory_and_branch_result_success_is_true(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_run_result = MagicMock()
        fake_run_result.returncode = 0
        fake_run_result.stdout = "develop\n"
        monkeypatch.setattr(
            "subprocess.run", lambda *a, **kw: fake_run_result, raising=True
        )
        async def fake_speak(**kwargs):
            return {"success": True, "played": True}
        monkeypatch.setattr(handlers, "speak_handler", fake_speak)
        # Act
        result = _run(handlers.announce_context_handler())
        # Act
        # Assert
        assert result["success"] is True

    def test_speaks_directory_and_branch_result_branch_develop(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_run_result = MagicMock()
        fake_run_result.returncode = 0
        fake_run_result.stdout = "develop\n"
        monkeypatch.setattr(
            "subprocess.run", lambda *a, **kw: fake_run_result, raising=True
        )
        async def fake_speak(**kwargs):
            return {"success": True, "played": True}
        monkeypatch.setattr(handlers, "speak_handler", fake_speak)
        # Act
        result = _run(handlers.announce_context_handler())
        # Act
        # Assert
        assert result["branch"] == "develop"

    def test_speaks_directory_and_branch_working_in_in_result_announced(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_run_result = MagicMock()
        fake_run_result.returncode = 0
        fake_run_result.stdout = "develop\n"
        monkeypatch.setattr(
            "subprocess.run", lambda *a, **kw: fake_run_result, raising=True
        )
        async def fake_speak(**kwargs):
            return {"success": True, "played": True}
        monkeypatch.setattr(handlers, "speak_handler", fake_speak)
        # Act
        result = _run(handlers.announce_context_handler())
        # Act
        # Assert
        assert "Working in" in result["announced"]

    def test_speaks_directory_and_branch_branch_develop_in_result_announced(self, monkeypatch):
        # Arrange
        from scitex_audio._mcp import handlers
        fake_run_result = MagicMock()
        fake_run_result.returncode = 0
        fake_run_result.stdout = "develop\n"
        monkeypatch.setattr(
            "subprocess.run", lambda *a, **kw: fake_run_result, raising=True
        )
        async def fake_speak(**kwargs):
            return {"success": True, "played": True}
        monkeypatch.setattr(handlers, "speak_handler", fake_speak)
        # Act
        result = _run(handlers.announce_context_handler())
        # Act
        # Assert
        assert "branch develop" in result["announced"]



# ---------------------------------------------------------------------------
# _emit_browser_speech (helper)
# ---------------------------------------------------------------------------


class TestEmitBrowserSpeech:
    def test_emits_osc_to_stderr_x1b_9999_speak_in_out(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            _emit_browser_speech("hello")
        # Act
        out = stderr.getvalue()
        # Act
        # Assert
        assert "\x1b]9999;speak:" in out

    def test_emits_osc_to_stderr_out_endswith_x07(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            _emit_browser_speech("hello")
        # Act
        out = stderr.getvalue()
        # Act
        # Assert
        assert out.endswith("\x07")


    def test_text_round_trips_through_base64(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech

        text = "test payload with unicode"
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            _emit_browser_speech(text)
        # Assert
        assert _decode_osc_text(stderr.getvalue()) == text

    def test_emits_to_stderr_not_stdout_x1b_9999_speak_not_in_stdout_getvalue(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Act
        with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            _emit_browser_speech("check stream")
        # Act
        # Assert
        assert "\x1b]9999;speak:" not in stdout.getvalue()

    def test_emits_to_stderr_not_stdout_x1b_9999_speak_in_stderr_getvalue(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Act
        with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            _emit_browser_speech("check stream")
        # Act
        # Assert
        assert "\x1b]9999;speak:" in stderr.getvalue()



# ---------------------------------------------------------------------------
# _get_signature (helper)
# ---------------------------------------------------------------------------


class TestGetSignature:
    def test_returns_dot_terminated_string_sig_is_str(self):
        # Arrange
        from scitex_audio._mcp.handlers import _get_signature
        # Act
        sig = _get_signature()
        # Act
        # Assert
        assert isinstance(sig, str)

    def test_returns_dot_terminated_string_sig_endswith(self):
        # Arrange
        from scitex_audio._mcp.handlers import _get_signature
        # Act
        sig = _get_signature()
        # Act
        # Assert
        assert sig.endswith(". ")

    def test_returns_dot_terminated_string_sig_count_2(self):
        # Arrange
        from scitex_audio._mcp.handlers import _get_signature
        # Act
        sig = _get_signature()
        # Act
        # Assert
        assert sig.count(". ") >= 2



# ---------------------------------------------------------------------------
# speak_handler — cloud-relay mode (SCITEX_CLOUD=true)
# ---------------------------------------------------------------------------


class TestSpeakHandlerCloudRelay:
    def test_emits_osc_escape_x1b_9999_speak_in_stderr_getvalue(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert "\x1b]9999;speak:" in stderr.getvalue()

    def test_emits_osc_escape_decode_osc_text_stderr_getvalue_hello_cloud(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert _decode_osc_text(stderr.getvalue()) == "hello cloud"

    def test_emits_osc_escape_result_backend_browser_relay(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert result["backend"] == "browser_relay"

    def test_emits_osc_escape_result_mode_cloud_relay(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert result["mode"] == "cloud_relay"

    def test_emits_osc_escape_result_success_is_true(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert result["success"] is True

    def test_emits_osc_escape_result_played_is_true(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        # Assert
        assert result["played"] is True


    def test_signature_prepends_to_emitted_text_decoded_equals_fake_sig_msg(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp import handlers
        stderr = io.StringIO()
        with patch.object(handlers, "_get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr):
                result = _run(handlers.speak_handler(text="msg", signature=True))
        # Act
        decoded = _decode_osc_text(stderr.getvalue())
        # Act
        # Assert
        assert decoded == fake_sig + "msg"

    def test_signature_prepends_to_emitted_text_result_signature_fake_sig(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp import handlers
        stderr = io.StringIO()
        with patch.object(handlers, "_get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr):
                result = _run(handlers.speak_handler(text="msg", signature=True))
        # Act
        decoded = _decode_osc_text(stderr.getvalue())
        # Act
        # Assert
        assert result["signature"] == fake_sig

    def test_signature_prepends_to_emitted_text_result_full_text_fake_sig_msg(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp import handlers
        stderr = io.StringIO()
        with patch.object(handlers, "_get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr):
                result = _run(handlers.speak_handler(text="msg", signature=True))
        # Act
        decoded = _decode_osc_text(stderr.getvalue())
        # Act
        # Assert
        assert result["full_text"] == fake_sig + "msg"


    def test_no_signature_omits_sig_keys_signature_not_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="no sig"))
        # Act
        # Assert
        assert "signature" not in result

    def test_no_signature_omits_sig_keys_full_text_not_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="no sig"))
        # Act
        # Assert
        assert "full_text" not in result



# ---------------------------------------------------------------------------
# speak_handler — local mode (SCITEX_CLOUD unset)
# ---------------------------------------------------------------------------


class TestSpeakHandlerLocal:
    def test_no_osc_in_local_mode(self, monkeypatch):
        # Arrange
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp import handlers

        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }
        stderr = io.StringIO()
        # Act
        with patch("sys.stderr", stderr):
            with patch.object(handlers.asyncio, "get_event_loop") as mock_loop_fn:
                mock_loop = MagicMock()
                mock_loop.run_in_executor = AsyncMock(return_value=local_result)
                mock_loop_fn.return_value = mock_loop
                _run(handlers.speak_handler(text="local"))
        # Assert
        assert "\x1b]9999;speak:" not in stderr.getvalue()

    def test_local_mode_does_not_return_cloud_relay_result_get_mode_cloud_relay(self, monkeypatch):
        # Arrange
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp import handlers
        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }
        # Act
        with patch.object(handlers.asyncio, "get_event_loop") as mock_loop_fn:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=local_result)
            mock_loop_fn.return_value = mock_loop
            result = _run(handlers.speak_handler(text="local mode check"))
        # Act
        # Assert
        assert result.get("mode") != "cloud_relay"

    def test_local_mode_does_not_return_cloud_relay_result_backend_gtts(self, monkeypatch):
        # Arrange
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp import handlers
        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }
        # Act
        with patch.object(handlers.asyncio, "get_event_loop") as mock_loop_fn:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=local_result)
            mock_loop_fn.return_value = mock_loop
            result = _run(handlers.speak_handler(text="local mode check"))
        # Act
        # Assert
        assert result["backend"] == "gtts"



if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
