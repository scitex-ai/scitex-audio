#!/usr/bin/env python3
"""Tests for scitex_audio._mcp.handlers (MCP server tool handlers).

No mocks: every handler exposes injectable seams (``speak_fn=``,
``available_fn=``/``fallback_order=``, ``get_tts_fn=``, ``player=``,
``status_fn=``, ``audio_dir=``, ``branch_resolver=``, ``signature_fn=``).
Tests pass small hand-rolled fakes and real ``tmp_path`` directories;
stderr is captured with ``contextlib.redirect_stderr`` and env vars use
yield-based save/restore fixtures.
"""

import asyncio
import base64
import contextlib
import io
import os
import time

import pytest

from scitex_audio._mcp import handlers
from scitex_audio._mcp.handlers import (
    _emit_browser_speech,
    _get_signature,
    speak_handler,
)


# --------------------------------------------------------------------------- #
# Helpers / fakes                                                             #
# --------------------------------------------------------------------------- #
def _decode_osc_text(stderr_output: str) -> str:
    """Extract and base64-decode the text carried in an OSC 9999 escape."""
    prefix = "\x1b]9999;speak:"
    suffix = "\x07"
    start = stderr_output.index(prefix) + len(prefix)
    end = stderr_output.index(suffix, start)
    b64 = stderr_output[start:end]
    return base64.b64decode(b64.encode()).decode()


def _run(coro):
    """Run a coroutine synchronously on a fresh event loop."""
    return asyncio.new_event_loop().run_until_complete(coro)


class _FakeVoiceEngine:
    """Stand-in for a TTS engine exposing only get_voices()."""

    def __init__(self, voices):
        self._voices = voices

    def get_voices(self):
        return list(self._voices)


@pytest.fixture
def cloud_env():
    """Force SCITEX_CLOUD=true for the duration of the test."""
    saved = os.environ.get("SCITEX_CLOUD")
    os.environ["SCITEX_CLOUD"] = "true"
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop("SCITEX_CLOUD", None)
        else:
            os.environ["SCITEX_CLOUD"] = saved


@pytest.fixture
def no_cloud_env():
    """Ensure SCITEX_CLOUD is unset for the duration of the test."""
    saved = os.environ.get("SCITEX_CLOUD")
    os.environ.pop("SCITEX_CLOUD", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["SCITEX_CLOUD"] = saved


# --------------------------------------------------------------------------- #
# generate_audio_handler                                                      #
# --------------------------------------------------------------------------- #
class TestGenerateAudioHandler:
    def test_generate_reports_success(self, tmp_path):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hello",
                output_path=str(out_file),
                speak_fn=lambda **kw: out_file,
            )
        )
        # Assert
        assert result["success"] is True

    def test_returns_output_path(self, tmp_path):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hello",
                output_path=str(out_file),
                speak_fn=lambda **kw: out_file,
            )
        )
        # Assert
        assert result["path"] == str(out_file)

    def test_generate_echoes_text(self, tmp_path):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hello",
                output_path=str(out_file),
                speak_fn=lambda **kw: out_file,
            )
        )
        # Assert
        assert result["text"] == "hello"

    def test_reports_nonnegative_size(self, tmp_path):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hello",
                output_path=str(out_file),
                speak_fn=lambda **kw: out_file,
            )
        )
        # Assert
        assert result["size_kb"] >= 0

    def test_failure_reports_not_success(self, tmp_path):
        # Arrange
        def boom(**kwargs):
            raise RuntimeError("boom")

        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hi", speak_fn=boom, audio_dir=tmp_path
            )
        )
        # Assert
        assert result["success"] is False

    def test_failure_surfaces_error_message(self, tmp_path):
        # Arrange
        def boom(**kwargs):
            raise RuntimeError("boom")

        # Act
        result = _run(
            handlers.generate_audio_handler(
                text="hi", speak_fn=boom, audio_dir=tmp_path
            )
        )
        # Assert
        assert "boom" in result["error"]


# --------------------------------------------------------------------------- #
# list_backends_handler                                                       #
# --------------------------------------------------------------------------- #
class TestListBackendsHandler:
    ORDER = ["elevenlabs", "luxtts", "gtts", "pyttsx3"]

    def test_list_backends_reports_success(self):
        # Arrange
        # Act
        result = _run(
            handlers.list_backends_handler(
                available_fn=lambda: ["gtts"], fallback_order=self.ORDER
            )
        )
        # Assert
        assert result["success"] is True

    def test_reports_available_backends(self):
        # Arrange
        # Act
        result = _run(
            handlers.list_backends_handler(
                available_fn=lambda: ["gtts"], fallback_order=self.ORDER
            )
        )
        # Assert
        assert result["available"] == ["gtts"]

    def test_default_is_first_available_in_order(self):
        # Arrange
        # Act
        result = _run(
            handlers.list_backends_handler(
                available_fn=lambda: ["gtts"], fallback_order=self.ORDER
            )
        )
        # Assert
        assert result["default"] == "gtts"

    def test_includes_backend_name_in_info(self):
        # Arrange
        # Act
        result = _run(
            handlers.list_backends_handler(
                available_fn=lambda: ["gtts"], fallback_order=self.ORDER
            )
        )
        # Assert
        names = {b["name"] for b in result["backends"]}
        assert "gtts" in names

    def test_no_backends_default_is_none(self):
        # Arrange
        # Act
        result = _run(
            handlers.list_backends_handler(
                available_fn=lambda: [], fallback_order=["gtts", "pyttsx3"]
            )
        )
        # Assert
        assert result["default"] is None


# --------------------------------------------------------------------------- #
# list_voices_handler                                                         #
# --------------------------------------------------------------------------- #
class TestListVoicesHandler:
    def test_list_voices_reports_success(self):
        # Arrange
        engine = _FakeVoiceEngine(["en", "fr", "ja"])
        # Act
        result = _run(
            handlers.list_voices_handler(
                backend="gtts", get_tts_fn=lambda backend: engine
            )
        )
        # Assert
        assert result["success"] is True

    def test_reports_voice_count(self):
        # Arrange
        engine = _FakeVoiceEngine(["en", "fr", "ja"])
        # Act
        result = _run(
            handlers.list_voices_handler(
                backend="gtts", get_tts_fn=lambda backend: engine
            )
        )
        # Assert
        assert result["count"] == 3

    def test_list_voices_echoes_backend(self):
        # Arrange
        engine = _FakeVoiceEngine(["en"])
        # Act
        result = _run(
            handlers.list_voices_handler(
                backend="gtts", get_tts_fn=lambda backend: engine
            )
        )
        # Assert
        assert result["backend"] == "gtts"

    def test_failure_reports_not_success(self):
        # Arrange
        def boom(backend):
            raise ValueError("no such backend")

        # Act
        result = _run(handlers.list_voices_handler(backend="nope", get_tts_fn=boom))
        # Assert
        assert result["success"] is False

    def test_failure_surfaces_error_message(self):
        # Arrange
        def boom(backend):
            raise ValueError("no such backend")

        # Act
        result = _run(handlers.list_voices_handler(backend="nope", get_tts_fn=boom))
        # Assert
        assert "no such backend" in result["error"]


# --------------------------------------------------------------------------- #
# play_audio_handler                                                          #
# --------------------------------------------------------------------------- #
class TestPlayAudioHandler:
    def test_missing_file_reports_not_success(self):
        # Arrange
        # Act
        result = _run(handlers.play_audio_handler(path="/no/such/file.wav"))
        # Assert
        assert result["success"] is False

    def test_missing_file_error_says_not_found(self):
        # Arrange
        # Act
        result = _run(handlers.play_audio_handler(path="/no/such/file.wav"))
        # Assert
        assert "not found" in result["error"].lower()

    def test_existing_file_reports_success(self, tmp_path):
        # Arrange
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        plays = []
        # Act
        result = _run(handlers.play_audio_handler(path=str(f), player=plays.append))
        # Assert
        assert result["success"] is True

    def test_existing_file_reports_played_path(self, tmp_path):
        # Arrange
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        # Act
        result = _run(handlers.play_audio_handler(path=str(f), player=lambda p: None))
        # Assert
        assert result["played"] == str(f)

    def test_existing_file_invokes_player_once(self, tmp_path):
        # Arrange
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        plays = []
        # Act
        _run(handlers.play_audio_handler(path=str(f), player=plays.append))
        # Assert
        assert len(plays) == 1


# --------------------------------------------------------------------------- #
# list_audio_files_handler                                                    #
# --------------------------------------------------------------------------- #
@pytest.fixture
def audio_dir_with_two(tmp_path):
    d = tmp_path / "audio"
    d.mkdir()
    (d / "a.mp3").write_bytes(b"hello")
    (d / "b.wav").write_bytes(b"world!")
    return d


class TestListAudioFilesHandler:
    def test_list_audio_files_reports_success(self, audio_dir_with_two):
        # Arrange
        # Act
        result = _run(
            handlers.list_audio_files_handler(limit=10, audio_dir=audio_dir_with_two)
        )
        # Assert
        assert result["success"] is True

    def test_list_files_counts_files(self, audio_dir_with_two):
        # Arrange
        # Act
        result = _run(
            handlers.list_audio_files_handler(limit=10, audio_dir=audio_dir_with_two)
        )
        # Assert
        assert result["count"] == 2

    def test_lists_both_file_names(self, audio_dir_with_two):
        # Arrange
        # Act
        result = _run(
            handlers.list_audio_files_handler(limit=10, audio_dir=audio_dir_with_two)
        )
        # Assert
        names = {f["name"] for f in result["files"]}
        assert names == {"a.mp3", "b.wav"}

    def test_limit_caps_count(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        for i in range(5):
            (d / f"f{i}.mp3").write_bytes(b"x")
        # Act
        result = _run(handlers.list_audio_files_handler(limit=2, audio_dir=d))
        # Assert
        assert result["count"] == 2


# --------------------------------------------------------------------------- #
# clear_audio_cache_handler                                                   #
# --------------------------------------------------------------------------- #
class TestClearAudioCacheHandler:
    def test_zero_age_clears_everything(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        (d / "a.mp3").write_bytes(b"x")
        (d / "b.wav").write_bytes(b"y")
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=0, audio_dir=d))
        # Assert
        assert result["deleted"] == 2

    def test_zero_age_leaves_no_mp3(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        (d / "a.mp3").write_bytes(b"x")
        (d / "b.wav").write_bytes(b"y")
        # Act
        _run(handlers.clear_audio_cache_handler(max_age_hours=0, audio_dir=d))
        # Assert
        assert list(d.glob("*.mp3")) == []

    def test_fresh_file_is_kept(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        f = d / "fresh.mp3"
        f.write_bytes(b"x")
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24, audio_dir=d))
        # Assert
        assert result["deleted"] == 0

    def test_fresh_file_still_exists(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        f = d / "fresh.mp3"
        f.write_bytes(b"x")
        # Act
        _run(handlers.clear_audio_cache_handler(max_age_hours=24, audio_dir=d))
        # Assert
        assert f.exists()

    def test_stale_file_is_deleted(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        f = d / "stale.mp3"
        f.write_bytes(b"x")
        old_ts = time.time() - 48 * 3_600
        os.utime(f, (old_ts, old_ts))
        # Act
        result = _run(handlers.clear_audio_cache_handler(max_age_hours=24, audio_dir=d))
        # Assert
        assert result["deleted"] == 1

    def test_stale_file_no_longer_exists(self, tmp_path):
        # Arrange
        d = tmp_path / "audio"
        d.mkdir()
        f = d / "stale.mp3"
        f.write_bytes(b"x")
        old_ts = time.time() - 48 * 3_600
        os.utime(f, (old_ts, old_ts))
        # Act
        _run(handlers.clear_audio_cache_handler(max_age_hours=24, audio_dir=d))
        # Assert
        assert not f.exists()


# --------------------------------------------------------------------------- #
# check_audio_status_handler                                                  #
# --------------------------------------------------------------------------- #
class TestCheckAudioStatusHandler:
    def test_check_audio_status_reports_success(self):
        # Arrange
        status = {"is_wsl": True, "recommended": "linux"}
        # Act
        result = _run(
            handlers.check_audio_status_handler(status_fn=lambda: dict(status))
        )
        # Assert
        assert result["success"] is True

    def test_passes_through_status_fields(self):
        # Arrange
        status = {"is_wsl": True, "recommended": "linux"}
        # Act
        result = _run(
            handlers.check_audio_status_handler(status_fn=lambda: dict(status))
        )
        # Assert
        assert result["is_wsl"] is True

    def test_check_status_adds_timestamp(self):
        # Arrange
        status = {"is_wsl": True, "recommended": "linux"}
        # Act
        result = _run(
            handlers.check_audio_status_handler(status_fn=lambda: dict(status))
        )
        # Assert
        assert "timestamp" in result


# --------------------------------------------------------------------------- #
# speech_queue_status_handler                                                 #
# --------------------------------------------------------------------------- #
class TestSpeechQueueStatusHandler:
    def test_speech_queue_status_reports_success(self):
        # Arrange
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Assert
        assert result["success"] is True

    def test_includes_locked_field(self):
        # Arrange
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Assert
        assert "locked" in result

    def test_includes_message_field(self):
        # Arrange
        # Act
        result = _run(handlers.speech_queue_status_handler())
        # Assert
        assert "message" in result


# --------------------------------------------------------------------------- #
# announce_context_handler                                                    #
# --------------------------------------------------------------------------- #
class TestAnnounceContextHandler:
    @staticmethod
    async def _fake_speak(**kwargs):
        return {"success": True, "played": True}

    def test_announce_context_reports_success(self):
        # Arrange
        # Act
        result = _run(
            handlers.announce_context_handler(
                branch_resolver=lambda cwd: "develop",
                speak_fn=TestAnnounceContextHandler._fake_speak,
            )
        )
        # Assert
        assert result["success"] is True

    def test_reports_resolved_branch(self):
        # Arrange
        # Act
        result = _run(
            handlers.announce_context_handler(
                branch_resolver=lambda cwd: "develop",
                speak_fn=TestAnnounceContextHandler._fake_speak,
            )
        )
        # Assert
        assert result["branch"] == "develop"

    def test_announcement_mentions_working_in(self):
        # Arrange
        # Act
        result = _run(
            handlers.announce_context_handler(
                branch_resolver=lambda cwd: "develop",
                speak_fn=TestAnnounceContextHandler._fake_speak,
            )
        )
        # Assert
        assert "Working in" in result["announced"]

    def test_announcement_mentions_branch(self):
        # Arrange
        # Act
        result = _run(
            handlers.announce_context_handler(
                branch_resolver=lambda cwd: "develop",
                speak_fn=TestAnnounceContextHandler._fake_speak,
            )
        )
        # Assert
        assert "branch develop" in result["announced"]

    def test_no_branch_omits_branch_phrase(self):
        # Arrange
        # Act
        result = _run(
            handlers.announce_context_handler(
                branch_resolver=lambda cwd: None,
                speak_fn=TestAnnounceContextHandler._fake_speak,
            )
        )
        # Assert
        assert "branch" not in result["announced"]


# --------------------------------------------------------------------------- #
# _emit_browser_speech (helper)                                               #
# --------------------------------------------------------------------------- #
class TestEmitBrowserSpeech:
    def test_emits_osc_prefix_to_stderr(self):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _emit_browser_speech("hello")
        # Assert
        assert "\x1b]9999;speak:" in stderr.getvalue()

    def test_output_ends_with_bell(self):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _emit_browser_speech("hello")
        # Assert
        assert stderr.getvalue().endswith("\x07")

    def test_text_round_trips_through_base64(self):
        # Arrange
        stderr = io.StringIO()
        text = "test payload with unicode"
        # Act
        with contextlib.redirect_stderr(stderr):
            _emit_browser_speech(text)
        # Assert
        assert _decode_osc_text(stderr.getvalue()) == text

    def test_does_not_write_to_stdout(self):
        # Arrange
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            _emit_browser_speech("check stream")
        # Assert
        assert "\x1b]9999;speak:" not in stdout.getvalue()


# --------------------------------------------------------------------------- #
# _get_signature (helper)                                                     #
# --------------------------------------------------------------------------- #
class TestGetSignature:
    def test_returns_a_string(self):
        # Arrange
        # Act
        sig = _get_signature()
        # Assert
        assert isinstance(sig, str)

    def test_ends_with_dot_space(self):
        # Arrange
        # Act
        sig = _get_signature()
        # Assert
        assert sig.endswith(". ")

    def test_has_at_least_two_segments(self):
        # Arrange
        # Act
        sig = _get_signature()
        # Assert
        assert sig.count(". ") >= 2


# --------------------------------------------------------------------------- #
# speak_handler — cloud-relay mode (SCITEX_CLOUD=true)                         #
# --------------------------------------------------------------------------- #
class TestSpeakHandlerCloudRelay:
    def test_emits_osc_escape(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _run(speak_handler(text="hello cloud"))
        # Assert
        assert "\x1b]9999;speak:" in stderr.getvalue()

    def test_emitted_text_matches_input(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _run(speak_handler(text="hello cloud"))
        # Assert
        assert _decode_osc_text(stderr.getvalue()) == "hello cloud"

    def test_backend_is_browser_relay(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Assert
        assert result["backend"] == "browser_relay"

    def test_mode_is_cloud_relay(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Assert
        assert result["mode"] == "cloud_relay"

    def test_speak_cloud_relay_reports_success(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Assert
        assert result["success"] is True

    def test_cloud_relay_reports_played(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="hello cloud"))
        # Assert
        assert result["played"] is True

    def test_signature_is_prepended_to_emitted_text(self, cloud_env):
        # Arrange
        fake_sig = "myhost. myproject. main. "
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _run(
                speak_handler(text="msg", signature=True, signature_fn=lambda: fake_sig)
            )
        # Assert
        assert _decode_osc_text(stderr.getvalue()) == fake_sig + "msg"

    def test_signature_field_in_result(self, cloud_env):
        # Arrange
        fake_sig = "myhost. myproject. main. "
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(
                speak_handler(text="msg", signature=True, signature_fn=lambda: fake_sig)
            )
        # Assert
        assert result["signature"] == fake_sig

    def test_full_text_field_in_result(self, cloud_env):
        # Arrange
        fake_sig = "myhost. myproject. main. "
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(
                speak_handler(text="msg", signature=True, signature_fn=lambda: fake_sig)
            )
        # Assert
        assert result["full_text"] == fake_sig + "msg"

    def test_no_signature_omits_signature_key(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="no sig"))
        # Assert
        assert "signature" not in result

    def test_no_signature_omits_full_text_key(self, cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            result = _run(speak_handler(text="no sig"))
        # Assert
        assert "full_text" not in result


# --------------------------------------------------------------------------- #
# speak_handler — local mode (SCITEX_CLOUD unset)                             #
# --------------------------------------------------------------------------- #
class TestSpeakHandlerLocal:
    LOCAL = {"success": True, "backend": "gtts", "played": True, "mode": "local"}

    def test_no_osc_in_local_mode(self, no_cloud_env):
        # Arrange
        stderr = io.StringIO()
        # Act
        with contextlib.redirect_stderr(stderr):
            _run(speak_handler(text="local", speak_fn=lambda **kw: dict(self.LOCAL)))
        # Assert
        assert "\x1b]9999;speak:" not in stderr.getvalue()

    def test_mode_is_not_cloud_relay(self, no_cloud_env):
        # Arrange
        # Act
        result = _run(
            speak_handler(text="local check", speak_fn=lambda **kw: dict(self.LOCAL))
        )
        # Assert
        assert result["mode"] != "cloud_relay"

    def test_backend_passes_through(self, no_cloud_env):
        # Arrange
        # Act
        result = _run(
            speak_handler(text="local check", speak_fn=lambda **kw: dict(self.LOCAL))
        )
        # Assert
        assert result["backend"] == "gtts"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
