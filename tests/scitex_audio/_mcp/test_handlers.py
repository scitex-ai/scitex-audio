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
    def test_returns_path_and_size(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")

        # tts_speak is imported lazily inside the handler; patch the module attr.
        def fake_speak(**kwargs):
            return out_file

        monkeypatch.setattr("scitex_audio.speak", fake_speak, raising=False)

        result = _run(
            handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        assert result["success"] is True
        assert result["path"] == str(out_file)
        assert result["text"] == "hello"
        assert result["size_kb"] >= 0

    def test_failure_returns_error(self, monkeypatch):
        from scitex_audio._mcp import handlers

        def boom(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr("scitex_audio.speak", boom, raising=False)
        result = _run(handlers.generate_audio_handler(text="hi"))
        assert result["success"] is False
        assert "boom" in result["error"]


# ---------------------------------------------------------------------------
# list_backends_handler
# ---------------------------------------------------------------------------


class TestListBackendsHandler:
    def test_reports_available_and_default(self, monkeypatch):
        from scitex_audio._mcp import handlers

        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: ["gtts"], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
            raising=False,
        )
        result = _run(handlers.list_backends_handler())
        assert result["success"] is True
        assert result["available"] == ["gtts"]
        assert result["default"] == "gtts"  # first available in FALLBACK_ORDER
        names = {b["name"] for b in result["backends"]}
        assert "gtts" in names

    def test_no_backends_default_is_none(self, monkeypatch):
        from scitex_audio._mcp import handlers

        monkeypatch.setattr(
            "scitex_audio.available_backends", lambda: [], raising=False
        )
        monkeypatch.setattr(
            "scitex_audio.FALLBACK_ORDER",
            ["gtts", "pyttsx3"],
            raising=False,
        )
        result = _run(handlers.list_backends_handler())
        assert result["success"] is True
        assert result["default"] is None


# ---------------------------------------------------------------------------
# list_voices_handler
# ---------------------------------------------------------------------------


class TestListVoicesHandler:
    def test_returns_voices(self, monkeypatch):
        from scitex_audio._mcp import handlers

        fake_tts = MagicMock()
        fake_tts.get_voices.return_value = ["en", "fr", "ja"]
        monkeypatch.setattr(
            "scitex_audio.get_tts", lambda backend: fake_tts, raising=False
        )
        result = _run(handlers.list_voices_handler(backend="gtts"))
        assert result["success"] is True
        assert result["count"] == 3
        assert result["backend"] == "gtts"

    def test_failure_returns_error(self, monkeypatch):
        from scitex_audio._mcp import handlers

        def boom(backend):
            raise ValueError("no such backend")

        monkeypatch.setattr("scitex_audio.get_tts", boom, raising=False)
        result = _run(handlers.list_voices_handler(backend="nope"))
        assert result["success"] is False
        assert "no such backend" in result["error"]


# ---------------------------------------------------------------------------
# play_audio_handler
# ---------------------------------------------------------------------------


class TestPlayAudioHandler:
    def test_missing_file_returns_error(self):
        from scitex_audio._mcp import handlers

        result = _run(handlers.play_audio_handler(path="/no/such/file.wav"))
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_existing_file_invokes_play(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        f = tmp_path / "ok.wav"
        f.write_bytes(b"")

        # _play_audio is a method of BaseTTS; bypass real audio call.
        from scitex_audio._engines._base import BaseTTS

        monkeypatch.setattr(BaseTTS, "_play_audio", lambda self, p: None, raising=False)

        result = _run(handlers.play_audio_handler(path=str(f)))
        assert result["success"] is True
        assert result["played"] == str(f)


# ---------------------------------------------------------------------------
# list_audio_files_handler
# ---------------------------------------------------------------------------


class TestListAudioFilesHandler:
    def test_lists_files(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        # Point _get_audio_dir at a tmpdir
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")

        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)

        result = _run(handlers.list_audio_files_handler(limit=10))
        assert result["success"] is True
        assert result["count"] == 2
        names = {f["name"] for f in result["files"]}
        assert names == {"a.mp3", "b.wav"}

    def test_limit_respected(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        for i in range(5):
            (audio_dir / f"f{i}.mp3").write_bytes(b"x")

        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        result = _run(handlers.list_audio_files_handler(limit=2))
        assert result["count"] == 2


# ---------------------------------------------------------------------------
# clear_audio_cache_handler
# ---------------------------------------------------------------------------


class TestClearAudioCacheHandler:
    def test_clears_all_when_max_age_zero(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)

        result = _run(handlers.clear_audio_cache_handler(max_age_hours=0))
        assert result["success"] is True
        assert result["deleted"] == 2
        assert not list(audio_dir.glob("*.mp3"))

    def test_keeps_fresh_files(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        # File is fresh (just created), so 24h cutoff should keep it.
        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)

        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        assert result["success"] is True
        assert result["deleted"] == 0
        assert f.exists()

    def test_deletes_stale_files(self, tmp_path, monkeypatch):
        from scitex_audio._mcp import handlers

        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        # Backdate mtime to 48h ago.
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))

        monkeypatch.setattr(handlers, "_get_audio_dir", lambda: audio_dir)
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24))
        assert result["success"] is True
        assert result["deleted"] == 1
        assert not f.exists()


# ---------------------------------------------------------------------------
# check_audio_status_handler
# ---------------------------------------------------------------------------


class TestCheckAudioStatusHandler:
    def test_wraps_check_wsl_audio(self, monkeypatch):
        from scitex_audio._mcp import handlers

        fake_status = {"is_wsl": True, "recommended": "linux"}
        monkeypatch.setattr(
            "scitex_audio.check_wsl_audio", lambda: dict(fake_status), raising=False
        )
        result = _run(handlers.check_audio_status_handler())
        assert result["success"] is True
        assert result["is_wsl"] is True
        assert "timestamp" in result


# ---------------------------------------------------------------------------
# speech_queue_status_handler
# ---------------------------------------------------------------------------


class TestSpeechQueueStatusHandler:
    def test_returns_success_envelope(self):
        from scitex_audio._mcp import handlers

        result = _run(handlers.speech_queue_status_handler())
        assert result["success"] is True
        assert "locked" in result
        assert "message" in result


# ---------------------------------------------------------------------------
# announce_context_handler
# ---------------------------------------------------------------------------


class TestAnnounceContextHandler:
    def test_speaks_directory_and_branch(self, monkeypatch):
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

        result = _run(handlers.announce_context_handler())
        assert result["success"] is True
        assert result["branch"] == "develop"
        assert "Working in" in result["announced"]
        assert "branch develop" in result["announced"]


# ---------------------------------------------------------------------------
# _emit_browser_speech (helper)
# ---------------------------------------------------------------------------


class TestEmitBrowserSpeech:
    def test_emits_osc_to_stderr(self):
        from scitex_audio._mcp.handlers import _emit_browser_speech

        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            _emit_browser_speech("hello")
        out = stderr.getvalue()
        assert "\x1b]9999;speak:" in out
        assert out.endswith("\x07")

    def test_text_round_trips_through_base64(self):
        from scitex_audio._mcp.handlers import _emit_browser_speech

        text = "test payload with unicode"
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            _emit_browser_speech(text)
        assert _decode_osc_text(stderr.getvalue()) == text

    def test_emits_to_stderr_not_stdout(self):
        from scitex_audio._mcp.handlers import _emit_browser_speech

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            _emit_browser_speech("check stream")
        assert "\x1b]9999;speak:" not in stdout.getvalue()
        assert "\x1b]9999;speak:" in stderr.getvalue()


# ---------------------------------------------------------------------------
# _get_signature (helper)
# ---------------------------------------------------------------------------


class TestGetSignature:
    def test_returns_dot_terminated_string(self):
        from scitex_audio._mcp.handlers import _get_signature

        sig = _get_signature()
        assert isinstance(sig, str)
        assert sig.endswith(". ")
        # Should at minimum have hostname + project parts
        assert sig.count(". ") >= 2


# ---------------------------------------------------------------------------
# speak_handler — cloud-relay mode (SCITEX_CLOUD=true)
# ---------------------------------------------------------------------------


class TestSpeakHandlerCloudRelay:
    def test_emits_osc_escape(self, monkeypatch):
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="hello cloud"))
        assert "\x1b]9999;speak:" in stderr.getvalue()
        assert _decode_osc_text(stderr.getvalue()) == "hello cloud"
        assert result["backend"] == "browser_relay"
        assert result["mode"] == "cloud_relay"
        assert result["success"] is True
        assert result["played"] is True

    def test_signature_prepends_to_emitted_text(self, monkeypatch):
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp import handlers

        stderr = io.StringIO()
        with patch.object(handlers, "_get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr):
                result = _run(handlers.speak_handler(text="msg", signature=True))

        decoded = _decode_osc_text(stderr.getvalue())
        assert decoded == fake_sig + "msg"
        assert result["signature"] == fake_sig
        assert result["full_text"] == fake_sig + "msg"

    def test_no_signature_omits_sig_keys(self, monkeypatch):
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            result = _run(speak_handler(text="no sig"))
        assert "signature" not in result
        assert "full_text" not in result


# ---------------------------------------------------------------------------
# speak_handler — local mode (SCITEX_CLOUD unset)
# ---------------------------------------------------------------------------


class TestSpeakHandlerLocal:
    def test_no_osc_in_local_mode(self, monkeypatch):
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp import handlers

        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with patch.object(handlers.asyncio, "get_event_loop") as mock_loop_fn:
                mock_loop = MagicMock()
                mock_loop.run_in_executor = AsyncMock(return_value=local_result)
                mock_loop_fn.return_value = mock_loop
                _run(handlers.speak_handler(text="local"))
        assert "\x1b]9999;speak:" not in stderr.getvalue()

    def test_local_mode_does_not_return_cloud_relay(self, monkeypatch):
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp import handlers

        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }
        with patch.object(handlers.asyncio, "get_event_loop") as mock_loop_fn:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=local_result)
            mock_loop_fn.return_value = mock_loop
            result = _run(handlers.speak_handler(text="local mode check"))
        assert result.get("mode") != "cloud_relay"
        assert result["backend"] == "gtts"


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
