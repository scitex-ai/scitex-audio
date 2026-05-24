#!/usr/bin/env python3
"""Tests for scitex_audio._mcp.handlers (MCP server tool handlers).

Mock-free rewrite covering the same handler surface as before:

  - generate_audio_handler
  - list_backends_handler
  - list_voices_handler
  - play_audio_handler
  - list_audio_files_handler
  - clear_audio_cache_handler
  - check_audio_status_handler
  - speech_queue_status_handler
  - announce_context_handler
  - speak_handler (cloud-relay path AND local path)
  - _emit_browser_speech (OSC escape semantics)
  - _get_signature (smoke)

The cloud-relay tests live here because the mirror file convention
(audit-project §2 PS204) puts all handlers.py coverage in one place.

Every monkeypatch / MagicMock / AsyncMock / patch.object is replaced
with a yield-based fixture that mutates module attributes directly
(restoring on teardown), or a hand-rolled fake exposing only the
surface the SUT touches.
"""

import asyncio
import base64
import io
import os
import sys
import time
from typing import Any

import pytest

import scitex_audio
import scitex_audio._mcp.handlers as _handlers
from scitex_audio._engines._base import BaseTTS


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


class _Swap:
    """Manages a stack of module-attribute swaps; reverses on teardown."""

    def __init__(self) -> None:
        self._undo: list = []

    def attr(self, obj, name, new):
        if hasattr(obj, name):
            original = getattr(obj, name)
            had_attr = True
        else:
            original = None
            had_attr = False
        setattr(obj, name, new)
        self._undo.append(
            lambda: setattr(obj, name, original)
            if had_attr
            else _delattr(obj, name)
        )

    def env(self, key, value):
        original = os.environ.get(key, "__NOT_SET__")
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
        self._undo.append(
            lambda: os.environ.pop(key, None)
            if original == "__NOT_SET__"
            else os.environ.__setitem__(key, original)
        )

    def teardown(self):
        for fn in reversed(self._undo):
            fn()
        self._undo.clear()


def _delattr(obj, name):
    try:
        delattr(obj, name)
    except AttributeError:
        pass


@pytest.fixture
def swap():
    helper = _Swap()
    try:
        yield helper
    finally:
        helper.teardown()


# ---------------------------------------------------------------------------
# generate_audio_handler
# ---------------------------------------------------------------------------


class TestGenerateAudioHandler:
    def test_returns_success_true_when_speak_returns_path(self, tmp_path, swap):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        swap.attr(scitex_audio, "speak", lambda **_: out_file)
        # Act
        result = _run(
            _handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Assert
        assert result["success"] is True

    def test_returns_path_as_string_from_handler(self, tmp_path, swap):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        swap.attr(scitex_audio, "speak", lambda **_: out_file)
        # Act
        result = _run(
            _handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Assert
        assert result["path"] == str(out_file)

    def test_returns_text_in_response_envelope(self, tmp_path, swap):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        swap.attr(scitex_audio, "speak", lambda **_: out_file)
        # Act
        result = _run(
            _handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Assert
        assert result["text"] == "hello"

    def test_returns_non_negative_size_kb_for_existing_file(self, tmp_path, swap):
        # Arrange
        out_file = tmp_path / "out.mp3"
        out_file.write_bytes(b"fake-mp3-bytes")
        swap.attr(scitex_audio, "speak", lambda **_: out_file)
        # Act
        result = _run(
            _handlers.generate_audio_handler(text="hello", output_path=str(out_file))
        )
        # Assert
        assert result["size_kb"] >= 0

    def test_speak_raises_returns_success_false_envelope(self, swap):
        # Arrange
        def boom(**_):
            raise RuntimeError("boom")

        swap.attr(scitex_audio, "speak", boom)
        # Act
        result = _run(_handlers.generate_audio_handler(text="hi"))
        # Assert
        assert result["success"] is False

    def test_speak_raises_returns_error_text_with_exception_message(self, swap):
        # Arrange
        def boom(**_):
            raise RuntimeError("boom")

        swap.attr(scitex_audio, "speak", boom)
        # Act
        result = _run(_handlers.generate_audio_handler(text="hi"))
        # Assert
        assert "boom" in result["error"]


# ---------------------------------------------------------------------------
# list_backends_handler
# ---------------------------------------------------------------------------


def _swap_backends(swap, available, order):
    swap.attr(scitex_audio, "available_backends", lambda: list(available))
    swap.attr(scitex_audio, "FALLBACK_ORDER", list(order))


class TestListBackendsHandler:
    def test_reports_success_true_when_one_backend_available(self, swap):
        # Arrange
        _swap_backends(swap, ["gtts"], ["elevenlabs", "luxtts", "gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        # Assert
        assert result["success"] is True

    def test_reports_available_list_matches_helper(self, swap):
        # Arrange
        _swap_backends(swap, ["gtts"], ["elevenlabs", "luxtts", "gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        # Assert
        assert result["available"] == ["gtts"]

    def test_default_is_first_available_in_fallback_order(self, swap):
        # Arrange
        _swap_backends(swap, ["gtts"], ["elevenlabs", "luxtts", "gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        # Assert
        assert result["default"] == "gtts"

    def test_backends_info_list_includes_known_name(self, swap):
        # Arrange
        _swap_backends(swap, ["gtts"], ["elevenlabs", "luxtts", "gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        names = {b["name"] for b in result["backends"]}
        # Assert
        assert "gtts" in names

    def test_no_backends_reports_success_true(self, swap):
        # Arrange
        _swap_backends(swap, [], ["gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        # Assert
        assert result["success"] is True

    def test_no_backends_reports_default_none(self, swap):
        # Arrange
        _swap_backends(swap, [], ["gtts", "pyttsx3"])
        # Act
        result = _run(_handlers.list_backends_handler())
        # Assert
        assert result["default"] is None


# ---------------------------------------------------------------------------
# list_voices_handler
# ---------------------------------------------------------------------------


class _FakeVoiceTTS:
    def __init__(self, voices):
        self._voices = voices

    def get_voices(self):
        return list(self._voices)


class TestListVoicesHandler:
    def test_returns_success_true_with_voices(self, swap):
        # Arrange
        swap.attr(scitex_audio, "get_tts", lambda backend: _FakeVoiceTTS(["en", "fr", "ja"]))
        # Act
        result = _run(_handlers.list_voices_handler(backend="gtts"))
        # Assert
        assert result["success"] is True

    def test_returns_voice_count_matching_get_voices(self, swap):
        # Arrange
        swap.attr(scitex_audio, "get_tts", lambda backend: _FakeVoiceTTS(["en", "fr", "ja"]))
        # Act
        result = _run(_handlers.list_voices_handler(backend="gtts"))
        # Assert
        assert result["count"] == 3

    def test_returns_backend_name_from_request(self, swap):
        # Arrange
        swap.attr(scitex_audio, "get_tts", lambda backend: _FakeVoiceTTS(["en"]))
        # Act
        result = _run(_handlers.list_voices_handler(backend="gtts"))
        # Assert
        assert result["backend"] == "gtts"

    def test_get_tts_raises_returns_success_false_envelope(self, swap):
        # Arrange
        def boom(backend):
            raise ValueError("no such backend")

        swap.attr(scitex_audio, "get_tts", boom)
        # Act
        result = _run(_handlers.list_voices_handler(backend="nope"))
        # Assert
        assert result["success"] is False

    def test_get_tts_raises_returns_error_text_with_exception_message(self, swap):
        # Arrange
        def boom(backend):
            raise ValueError("no such backend")

        swap.attr(scitex_audio, "get_tts", boom)
        # Act
        result = _run(_handlers.list_voices_handler(backend="nope"))
        # Assert
        assert "no such backend" in result["error"]


# ---------------------------------------------------------------------------
# play_audio_handler
# ---------------------------------------------------------------------------


class TestPlayAudioHandler:
    def test_missing_file_returns_success_false(self):
        # Arrange
        # Act
        result = _run(_handlers.play_audio_handler(path="/no/such/file.wav"))
        # Assert
        assert result["success"] is False

    def test_missing_file_error_message_mentions_not_found(self):
        # Arrange
        # Act
        result = _run(_handlers.play_audio_handler(path="/no/such/file.wav"))
        # Assert
        assert "not found" in result["error"].lower()

    def test_existing_file_returns_success_true(self, tmp_path, swap):
        # Arrange
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        swap.attr(BaseTTS, "_play_audio", lambda self, p, **kw: None)
        # Act
        result = _run(_handlers.play_audio_handler(path=str(f)))
        # Assert
        assert result["success"] is True

    def test_existing_file_response_path_matches_input(self, tmp_path, swap):
        # Arrange
        f = tmp_path / "ok.wav"
        f.write_bytes(b"")
        swap.attr(BaseTTS, "_play_audio", lambda self, p, **kw: None)
        # Act
        result = _run(_handlers.play_audio_handler(path=str(f)))
        # Assert
        assert result["played"] == str(f)


# ---------------------------------------------------------------------------
# list_audio_files_handler
# ---------------------------------------------------------------------------


class TestListAudioFilesHandler:
    def test_lists_files_returns_success_true(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.list_audio_files_handler(limit=10))
        # Assert
        assert result["success"] is True

    def test_lists_files_count_matches_tree_content(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.list_audio_files_handler(limit=10))
        # Assert
        assert result["count"] == 2

    def test_lists_files_names_match_disk_content(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"hello")
        (audio_dir / "b.wav").write_bytes(b"world!")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.list_audio_files_handler(limit=10))
        names = {f["name"] for f in result["files"]}
        # Assert
        assert names == {"a.mp3", "b.wav"}

    def test_limit_respected_when_more_files_present(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        for i in range(5):
            (audio_dir / f"f{i}.mp3").write_bytes(b"x")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.list_audio_files_handler(limit=2))
        # Assert
        assert result["count"] == 2


# ---------------------------------------------------------------------------
# clear_audio_cache_handler
# ---------------------------------------------------------------------------


class TestClearAudioCacheHandler:
    def test_max_age_zero_returns_success_true(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=0))
        # Assert
        assert result["success"] is True

    def test_max_age_zero_reports_deleted_count_matching_files(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=0))
        # Assert
        assert result["deleted"] == 2

    def test_max_age_zero_removes_mp3_files_from_disk(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "a.mp3").write_bytes(b"x")
        (audio_dir / "b.wav").write_bytes(b"y")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        _run(_handlers.clear_audio_cache_handler(max_age_hours=0))
        # Assert
        assert not list(audio_dir.glob("*.mp3"))

    def test_keeps_fresh_files_returns_success_true(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert result["success"] is True

    def test_keeps_fresh_files_reports_zero_deleted(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert result["deleted"] == 0

    def test_keeps_fresh_files_leaves_file_on_disk(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "fresh.mp3"
        f.write_bytes(b"x")
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert f.exists()

    def test_deletes_stale_files_returns_success_true(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert result["success"] is True

    def test_deletes_stale_files_reports_deleted_count_one(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        result = _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert result["deleted"] == 1

    def test_deletes_stale_files_removes_file_from_disk(self, tmp_path, swap):
        # Arrange
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        f = audio_dir / "stale.mp3"
        f.write_bytes(b"x")
        old_ts = time.time() - 48 * 3600
        os.utime(f, (old_ts, old_ts))
        swap.attr(_handlers, "_get_audio_dir", lambda: audio_dir)
        # Act
        _run(_handlers.clear_audio_cache_handler(max_age_hours=24))
        # Assert
        assert not f.exists()


# ---------------------------------------------------------------------------
# check_audio_status_handler
# ---------------------------------------------------------------------------


class TestCheckAudioStatusHandler:
    def test_check_wsl_audio_wraps_result_with_success_true(self, swap):
        # Arrange
        fake_status = {"is_wsl": True, "recommended": "linux"}
        swap.attr(scitex_audio, "check_wsl_audio", lambda: dict(fake_status))
        # Act
        result = _run(_handlers.check_audio_status_handler())
        # Assert
        assert result["success"] is True

    def test_check_wsl_audio_passes_is_wsl_value_through(self, swap):
        # Arrange
        fake_status = {"is_wsl": True, "recommended": "linux"}
        swap.attr(scitex_audio, "check_wsl_audio", lambda: dict(fake_status))
        # Act
        result = _run(_handlers.check_audio_status_handler())
        # Assert
        assert result["is_wsl"] is True

    def test_check_wsl_audio_appends_timestamp_key(self, swap):
        # Arrange
        fake_status = {"is_wsl": True, "recommended": "linux"}
        swap.attr(scitex_audio, "check_wsl_audio", lambda: dict(fake_status))
        # Act
        result = _run(_handlers.check_audio_status_handler())
        # Assert
        assert "timestamp" in result


# ---------------------------------------------------------------------------
# speech_queue_status_handler
# ---------------------------------------------------------------------------


class TestSpeechQueueStatusHandler:
    def test_returns_success_true_envelope(self):
        # Arrange
        # Act
        result = _run(_handlers.speech_queue_status_handler())
        # Assert
        assert result["success"] is True

    def test_returns_locked_key_in_envelope(self):
        # Arrange
        # Act
        result = _run(_handlers.speech_queue_status_handler())
        # Assert
        assert "locked" in result

    def test_returns_message_key_in_envelope(self):
        # Arrange
        # Act
        result = _run(_handlers.speech_queue_status_handler())
        # Assert
        assert "message" in result


# ---------------------------------------------------------------------------
# announce_context_handler
# ---------------------------------------------------------------------------


class _FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="develop\n"):
        self.returncode = returncode
        self.stdout = stdout


class TestAnnounceContextHandler:
    def test_announce_context_returns_success_true(self, swap):
        # Arrange
        import subprocess as _subprocess

        swap.attr(_subprocess, "run", lambda *a, **kw: _FakeCompletedProcess())

        async def fake_speak(**_):
            return {"success": True, "played": True}

        swap.attr(_handlers, "speak_handler", fake_speak)
        # Act
        result = _run(_handlers.announce_context_handler())
        # Assert
        assert result["success"] is True

    def test_announce_context_reports_branch_from_git_output(self, swap):
        # Arrange
        import subprocess as _subprocess

        swap.attr(_subprocess, "run", lambda *a, **kw: _FakeCompletedProcess())

        async def fake_speak(**_):
            return {"success": True, "played": True}

        swap.attr(_handlers, "speak_handler", fake_speak)
        # Act
        result = _run(_handlers.announce_context_handler())
        # Assert
        assert result["branch"] == "develop"

    def test_announce_context_announced_text_starts_with_working_in(self, swap):
        # Arrange
        import subprocess as _subprocess

        swap.attr(_subprocess, "run", lambda *a, **kw: _FakeCompletedProcess())

        async def fake_speak(**_):
            return {"success": True, "played": True}

        swap.attr(_handlers, "speak_handler", fake_speak)
        # Act
        result = _run(_handlers.announce_context_handler())
        # Assert
        assert "Working in" in result["announced"]

    def test_announce_context_announced_text_mentions_branch(self, swap):
        # Arrange
        import subprocess as _subprocess

        swap.attr(_subprocess, "run", lambda *a, **kw: _FakeCompletedProcess())

        async def fake_speak(**_):
            return {"success": True, "played": True}

        swap.attr(_handlers, "speak_handler", fake_speak)
        # Act
        result = _run(_handlers.announce_context_handler())
        # Assert
        assert "branch develop" in result["announced"]


# ---------------------------------------------------------------------------
# _emit_browser_speech (helper)
# ---------------------------------------------------------------------------


class _StderrCapture:
    """yield-based fixture helper that captures sys.stderr writes."""

    def __init__(self) -> None:
        self.buf = io.StringIO()
        self._original = sys.stderr

    def __enter__(self):
        sys.stderr = self.buf
        return self.buf

    def __exit__(self, *args):
        sys.stderr = self._original
        return False


class TestEmitBrowserSpeech:
    def test_emits_osc_prefix_to_stderr(self):
        # Arrange
        with _StderrCapture() as buf:
            _handlers._emit_browser_speech("hello")
            captured = buf.getvalue()
        # Act
        prefix_seen = "\x1b]9999;speak:" in captured
        # Assert
        assert prefix_seen is True

    def test_emits_osc_suffix_terminator_at_end(self):
        # Arrange
        with _StderrCapture() as buf:
            _handlers._emit_browser_speech("hello")
            captured = buf.getvalue()
        # Act
        ends_with_bel = captured.endswith("\x07")
        # Assert
        assert ends_with_bel is True

    def test_text_round_trips_through_base64_decoder(self):
        # Arrange
        text = "test payload with unicode"
        with _StderrCapture() as buf:
            _handlers._emit_browser_speech(text)
            captured = buf.getvalue()
        # Act
        decoded = _decode_osc_text(captured)
        # Assert
        assert decoded == text

    def test_does_not_emit_osc_prefix_to_stdout(self):
        # Arrange
        original_stdout = sys.stdout
        out = io.StringIO()
        sys.stdout = out
        try:
            with _StderrCapture():
                _handlers._emit_browser_speech("check stream")
        finally:
            sys.stdout = original_stdout
        # Act
        prefix_in_stdout = "\x1b]9999;speak:" in out.getvalue()
        # Assert
        assert prefix_in_stdout is False

    def test_does_emit_osc_prefix_to_stderr(self):
        # Arrange
        original_stdout = sys.stdout
        out = io.StringIO()
        sys.stdout = out
        try:
            with _StderrCapture() as buf:
                _handlers._emit_browser_speech("check stream")
                captured = buf.getvalue()
        finally:
            sys.stdout = original_stdout
        # Act
        prefix_in_stderr = "\x1b]9999;speak:" in captured
        # Assert
        assert prefix_in_stderr is True


# ---------------------------------------------------------------------------
# _get_signature (helper)
# ---------------------------------------------------------------------------


class TestGetSignature:
    def test_signature_returns_string_type(self):
        # Arrange
        # Act
        sig = _handlers._get_signature()
        # Assert
        assert isinstance(sig, str)

    def test_signature_ends_with_dot_space_separator(self):
        # Arrange
        # Act
        sig = _handlers._get_signature()
        # Assert
        assert sig.endswith(". ")

    def test_signature_has_at_least_two_dot_segments(self):
        # Arrange
        # Act
        sig = _handlers._get_signature()
        # Assert
        assert sig.count(". ") >= 2


# ---------------------------------------------------------------------------
# speak_handler — cloud-relay mode (SCITEX_CLOUD=true)
# ---------------------------------------------------------------------------


class TestSpeakHandlerCloudRelay:
    def test_cloud_mode_emits_osc_prefix_to_stderr(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        with _StderrCapture() as buf:
            _run(_handlers.speak_handler(text="hello cloud"))
            captured = buf.getvalue()
        # Act
        prefix_seen = "\x1b]9999;speak:" in captured
        # Assert
        assert prefix_seen is True

    def test_cloud_mode_emitted_payload_decodes_to_input_text(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        with _StderrCapture() as buf:
            _run(_handlers.speak_handler(text="hello cloud"))
            captured = buf.getvalue()
        # Act
        decoded = _decode_osc_text(captured)
        # Assert
        assert decoded == "hello cloud"

    def test_cloud_mode_returns_browser_relay_backend(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="hello cloud"))
        # Assert
        assert result["backend"] == "browser_relay"

    def test_cloud_mode_returns_cloud_relay_mode_string(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="hello cloud"))
        # Assert
        assert result["mode"] == "cloud_relay"

    def test_cloud_mode_returns_success_true(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="hello cloud"))
        # Assert
        assert result["success"] is True

    def test_cloud_mode_returns_played_true(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="hello cloud"))
        # Assert
        assert result["played"] is True

    def test_signature_prepends_to_payload_when_signature_true(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        swap.attr(_handlers, "_get_signature", lambda: fake_sig)
        with _StderrCapture() as buf:
            _run(_handlers.speak_handler(text="msg", signature=True))
            captured = buf.getvalue()
        # Act
        decoded = _decode_osc_text(captured)
        # Assert
        assert decoded == fake_sig + "msg"

    def test_signature_returned_in_envelope_when_signature_true(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        swap.attr(_handlers, "_get_signature", lambda: fake_sig)
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="msg", signature=True))
        # Assert
        assert result["signature"] == fake_sig

    def test_full_text_returned_in_envelope_when_signature_true(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        swap.attr(_handlers, "_get_signature", lambda: fake_sig)
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="msg", signature=True))
        # Assert
        assert result["full_text"] == fake_sig + "msg"

    def test_no_signature_kwarg_omits_signature_key_in_envelope(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="no sig"))
        # Assert
        assert "signature" not in result

    def test_no_signature_kwarg_omits_full_text_key_in_envelope(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", "true")
        # Act
        with _StderrCapture():
            result = _run(_handlers.speak_handler(text="no sig"))
        # Assert
        assert "full_text" not in result


# ---------------------------------------------------------------------------
# speak_handler — local mode (SCITEX_CLOUD unset)
# ---------------------------------------------------------------------------


_LOCAL_SPEAK_RESULT = {
    "success": True,
    "backend": "gtts",
    "played": True,
    "mode": "local",
}


class TestSpeakHandlerLocal:
    def test_local_mode_does_not_emit_osc_to_stderr(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", None)
        swap.attr(scitex_audio, "speak", lambda **_: dict(_LOCAL_SPEAK_RESULT))
        with _StderrCapture() as buf:
            _run(_handlers.speak_handler(text="local"))
            captured = buf.getvalue()
        # Act
        prefix_in_stderr = "\x1b]9999;speak:" in captured
        # Assert
        assert prefix_in_stderr is False

    def test_local_mode_response_mode_is_not_cloud_relay(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", None)
        swap.attr(scitex_audio, "speak", lambda **_: dict(_LOCAL_SPEAK_RESULT))
        # Act
        result = _run(_handlers.speak_handler(text="local mode check"))
        # Assert
        assert result.get("mode") != "cloud_relay"

    def test_local_mode_response_backend_is_gtts(self, swap):
        # Arrange
        swap.env("SCITEX_CLOUD", None)
        swap.attr(scitex_audio, "speak", lambda **_: dict(_LOCAL_SPEAK_RESULT))
        # Act
        result = _run(_handlers.speak_handler(text="local mode check"))
        # Assert
        assert result["backend"] == "gtts"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
