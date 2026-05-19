#!/usr/bin/env python3
"""Tests for cloud relay mode in scitex/audio/_mcp/handlers.py

When the environment variable SCITEX_CLOUD=true is set, speak_handler()
must emit an OSC escape sequence to stderr instead of playing audio locally:
    \\x1b]9999;speak:<base64-text>\\x07

Source file: src/scitex/audio/_mcp/handlers.py
"""

import asyncio
import base64
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _decode_osc_text(stderr_output: str) -> str:
    """Extract and base64-decode the text carried in an OSC 9999 escape."""
    prefix = "\x1b]9999;speak:"
    suffix = "\x07"
    assert prefix in stderr_output, f"OSC prefix not found in: {repr(stderr_output)}"
    start = stderr_output.index(prefix) + len(prefix)
    end = stderr_output.index(suffix, start)
    b64 = stderr_output[start:end]
    return base64.b64decode(b64.encode()).decode()


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Tests for _emit_browser_speech
# ---------------------------------------------------------------------------


class TestEmitBrowserSpeech:
    """Unit tests for the _emit_browser_speech helper."""

    def test_emits_osc_escape_sequence_x1b_9999_speak_in_output(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            _emit_browser_speech("hello")
        # Act
        output = stderr_capture.getvalue()
        # Act
        # Assert
        assert "\x1b]9999;speak:" in output

    def test_emits_osc_escape_sequence_output_endswith_x07(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            _emit_browser_speech("hello")
        # Act
        output = stderr_capture.getvalue()
        # Act
        # Assert
        assert output.endswith("\x07")


    def test_emitted_text_is_base64_encoded(self):
        """The text embedded in the OSC escape must be valid base64 for the input."""
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech

        input_text = "test payload"
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            _emit_browser_speech(input_text)

        # Act
        decoded = _decode_osc_text(stderr_capture.getvalue())
        # Assert
        assert decoded == input_text

    def test_emits_to_stderr_not_stdout_x1b_9999_speak_not_in_stdout_capture_getvalue(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stdout", stdout_capture), patch("sys.stderr", stderr_capture):
            _emit_browser_speech("check stream")
        # Act
        # Assert
        assert "\x1b]9999;speak:" not in stdout_capture.getvalue()

    def test_emits_to_stderr_not_stdout_x1b_9999_speak_in_stderr_capture_getvalue(self):
        # Arrange
        from scitex_audio._mcp.handlers import _emit_browser_speech
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stdout", stdout_capture), patch("sys.stderr", stderr_capture):
            _emit_browser_speech("check stream")
        # Act
        # Assert
        assert "\x1b]9999;speak:" in stderr_capture.getvalue()



# ---------------------------------------------------------------------------
# Tests for speak_handler in cloud relay mode
# ---------------------------------------------------------------------------


class TestSpeakHandlerCloudRelayMode:
    """speak_handler cloud relay: SCITEX_CLOUD=true path."""

    def test_cloud_relay_emits_osc_escape_x1b_9999_speak_in_output(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        output = stderr_capture.getvalue()
        # Act
        # Assert
        assert "\x1b]9999;speak:" in output

    def test_cloud_relay_emits_osc_escape_decoded_equals_hello_cloud_x1b_9999_speak_in_output(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        output = stderr_capture.getvalue()
        # Act
        # Assert
        assert "\x1b]9999;speak:" in output

    def test_cloud_relay_emits_osc_escape_decoded_equals_hello_cloud_decoded_equals_hello_cloud(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="hello cloud"))
        # Act
        output = stderr_capture.getvalue()
        # Assert
        assert "\x1b]9999;speak:" in output
        decoded = _decode_osc_text(output)
        # Act
        # Assert
        assert decoded == "hello cloud"



    def test_cloud_relay_returns_browser_relay_backend(self, monkeypatch):
        """Result dict must have backend='browser_relay' in cloud relay mode."""
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="check backend"))

        # Assert
        assert result["backend"] == "browser_relay"

    def test_cloud_relay_returns_cloud_relay_mode(self, monkeypatch):
        """Result dict must have mode='cloud_relay' in cloud relay mode."""
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="check mode"))

        # Assert
        assert result["mode"] == "cloud_relay"

    def test_cloud_relay_returns_success_true(self, monkeypatch):
        """Result dict must have success=True in cloud relay mode."""
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="check success"))

        # Assert
        assert result["success"] is True

    def test_cloud_relay_returns_played_true(self, monkeypatch):
        """Result dict must mark played=True even though audio is relayed, not local."""
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler

        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="check played"))

        # Assert
        assert result["played"] is True

    def test_cloud_relay_with_signature_prepends_to_emitted_text_decoded_startswith_fake_sig(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="important message", signature=True))
        # Act
        decoded = _decode_osc_text(stderr_capture.getvalue())
        # Act
        # Assert
        assert decoded.startswith(fake_sig)

    def test_cloud_relay_with_signature_prepends_to_emitted_text_important_message_in_decoded(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="important message", signature=True))
        # Act
        decoded = _decode_osc_text(stderr_capture.getvalue())
        # Act
        # Assert
        assert "important message" in decoded


    def test_cloud_relay_with_signature_populates_result_fields_signature_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="sig test", signature=True))
        # Act
        # Assert
        assert "signature" in result

    def test_cloud_relay_with_signature_populates_result_fields_full_text_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="sig test", signature=True))
        # Act
        # Assert
        assert "full_text" in result

    def test_cloud_relay_with_signature_populates_result_fields_result_signature_fake_sig(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="sig test", signature=True))
        # Act
        # Assert
        assert result["signature"] == fake_sig

    def test_cloud_relay_with_signature_populates_result_fields_result_full_text_fake_sig_sig_test(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        fake_sig = "myhost. myproject. main. "
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("scitex_audio._mcp.handlers._get_signature", return_value=fake_sig):
            with patch("sys.stderr", stderr_capture):
                result = _run(speak_handler(text="sig test", signature=True))
        # Act
        # Assert
        assert result["full_text"] == fake_sig + "sig test"


    def test_cloud_relay_without_signature_no_sig_keys_signature_not_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="no sig test"))
        # Act
        # Assert
        assert "signature" not in result

    def test_cloud_relay_without_signature_no_sig_keys_full_text_not_in_result(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("SCITEX_CLOUD", "true")
        from scitex_audio._mcp.handlers import speak_handler
        stderr_capture = io.StringIO()
        # Act
        with patch("sys.stderr", stderr_capture):
            result = _run(speak_handler(text="no sig test"))
        # Act
        # Assert
        assert "full_text" not in result



# ---------------------------------------------------------------------------
# Tests for speak_handler in local mode
# ---------------------------------------------------------------------------


class TestSpeakHandlerLocalMode:
    """speak_handler local mode: SCITEX_CLOUD not set."""

    def test_local_mode_does_not_emit_osc_escape(self, monkeypatch):
        """Without SCITEX_CLOUD, no OSC escape must appear on stderr."""
        # Arrange
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp.handlers import speak_handler

        mock_speak_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }

        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            with patch(
                "scitex_audio._mcp.handlers.asyncio.get_event_loop"
            ) as mock_loop_fn:
                mock_loop = MagicMock()
                mock_loop.run_in_executor = AsyncMock(return_value=mock_speak_result)
                mock_loop_fn.return_value = mock_loop
                _run(speak_handler(text="local speech"))

        # Act
        output = stderr_capture.getvalue()
        # Assert
        assert "\x1b]9999;speak:" not in output

    def test_local_mode_does_not_return_cloud_relay_mode(self, monkeypatch):
        """Local mode result must not have mode='cloud_relay'."""
        # Arrange
        monkeypatch.delenv("SCITEX_CLOUD", raising=False)
        from scitex_audio._mcp.handlers import speak_handler

        local_result = {
            "success": True,
            "backend": "gtts",
            "played": True,
            "mode": "local",
        }

        # Act
        with patch("scitex_audio._mcp.handlers.asyncio.get_event_loop") as mock_loop_fn:
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=local_result)
            mock_loop_fn.return_value = mock_loop
            result = _run(speak_handler(text="local mode check"))

        # Assert
        assert result.get("mode") != "cloud_relay"


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])
