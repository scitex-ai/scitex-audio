#!/usr/bin/env python3
"""Tests for scitex_audio._cli._main (Click root group + leaf commands).

Covers the surface area of the `scitex-audio` CLI:
  - root help, --version, --help-recursive, --json
  - speak-text option plumbing (mocked backend)
  - list-backends rendering (text + --json)
  - check-backends, stop-playback dry-run, transcribe-audio, show-env-template
  - deprecated redirects exit non-zero with hint
  - list-python-apis runs end-to-end

These exercise the public CLI shape an agent would invoke; backend calls
that need network / hardware are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scitex_audio._cli._main import audio


@pytest.fixture
def runner():
    return CliRunner()


class TestRootGroup:
    def test_help(self, runner):
        result = runner.invoke(audio, ["--help"])
        assert result.exit_code == 0
        assert "Text-to-speech" in result.output
        # §6b config-precedence chain documented in root docstring
        assert "config.yaml" in result.output
        assert "SCITEX_AUDIO_CONFIG" in result.output

    def test_version(self, runner):
        result = runner.invoke(audio, ["--version"])
        assert result.exit_code == 0
        assert "scitex-audio" in result.output

    def test_short_version_flag(self, runner):
        result = runner.invoke(audio, ["-V"])
        assert result.exit_code == 0
        assert "scitex-audio" in result.output

    def test_no_args_shows_help(self, runner):
        result = runner.invoke(audio, [])
        assert result.exit_code == 0
        assert "speak" in result.output.lower()

    def test_help_recursive(self, runner):
        result = runner.invoke(audio, ["--help-recursive"])
        assert result.exit_code == 0
        # Should mention multiple subcommands, indicating recursion happened.
        assert "speak-text" in result.output
        assert "list-backends" in result.output

    def test_root_json(self, runner):
        result = runner.invoke(audio, ["--json"])
        assert result.exit_code == 0
        # JSON envelope or fallback dict — either way must mention a known cmd
        assert "speak-text" in result.output or "list-backends" in result.output


class TestSpeakText:
    def test_speak_text_calls_backend(self, runner):
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello"])
        mock_speak.assert_called_once()
        kwargs = mock_speak.call_args[1]
        assert kwargs["text"] == "Hello"
        assert kwargs["play"] is True
        assert kwargs["fallback"] is True

    def test_speak_text_backend_option(self, runner):
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "-b", "gtts"])
        assert mock_speak.call_args[1]["backend"] == "gtts"

    def test_speak_text_invalid_backend_rejected(self, runner):
        result = runner.invoke(audio, ["speak-text", "Hi", "-b", "invalid"])
        assert result.exit_code != 0

    def test_speak_text_no_play_flag(self, runner):
        mock_speak = MagicMock(return_value={})
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "--no-play"])
        assert mock_speak.call_args[1]["play"] is False

    def test_speak_text_no_fallback_flag(self, runner):
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "--no-fallback"])
        assert mock_speak.call_args[1]["fallback"] is False


class TestListBackends:
    def test_text_output(self, runner):
        mock_avail = MagicMock(return_value=["gtts"])
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends"])
        assert result.exit_code == 0
        assert "available" in result.output.lower()

    def test_json_envelope(self, runner):
        mock_avail = MagicMock(return_value=["gtts", "pyttsx3"])
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends", "--json"])
        assert result.exit_code == 0
        # The Result envelope may be wrapped, but the data fields should appear
        assert "available" in result.output
        assert "fallback_order" in result.output


class TestCheckBackends:
    def test_runs_text(self, runner):
        mock_status = {
            "is_wsl": False,
            "wslg_available": False,
            "pulse_server_exists": False,
            "pulse_connected": False,
            "windows_fallback_available": False,
            "recommended": "linux",
        }
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends"])
        assert result.exit_code == 0
        assert "Audio Status Check" in result.output

    def test_runs_json(self, runner):
        mock_status = {
            "is_wsl": True,
            "wslg_available": True,
            "pulse_server_exists": True,
            "pulse_connected": True,
            "windows_fallback_available": True,
            "recommended": "linux",
        }
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends", "--json"])
        assert result.exit_code == 0
        assert "is_wsl" in result.output


class TestStopPlayback:
    def test_dry_run(self, runner):
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_calls_stop_speech(self, runner):
        mock_stop = MagicMock()
        with patch("scitex_audio.stop_speech", mock_stop):
            result = runner.invoke(audio, ["stop-playback"])
        assert result.exit_code == 0
        mock_stop.assert_called_once()


class TestTranscribeAudio:
    def test_calls_transcribe(self, runner, tmp_path):
        # transcribe-audio takes a Click Path(exists=True), so we need a real file
        audio_file = tmp_path / "x.wav"
        audio_file.write_bytes(b"")
        mock_transcribe = MagicMock(return_value={"success": True, "text": "hello"})
        with patch("scitex_audio.transcribe", mock_transcribe):
            result = runner.invoke(audio, ["transcribe-audio", str(audio_file)])
        assert result.exit_code == 0
        assert "hello" in result.output


class TestShowEnvTemplate:
    def test_stdout(self, runner):
        result = runner.invoke(audio, ["show-env-template"])
        assert result.exit_code == 0
        # Template should mention something about SCITEX_AUDIO env vars
        assert len(result.output) > 0

    def test_no_sensitive(self, runner):
        result = runner.invoke(audio, ["show-env-template", "--no-sensitive"])
        assert result.exit_code == 0


class TestDeprecatedRedirects:
    @pytest.mark.parametrize(
        "old,new",
        [
            ("speak", "speak-text"),
            ("backends", "list-backends"),
            ("check", "check-backends"),
            ("stop", "stop-playback"),
            ("transcribe", "transcribe-audio"),
            ("env-template", "show-env-template"),
        ],
    )
    def test_old_command_exits_with_hint(self, runner, old, new):
        result = runner.invoke(audio, [old, "anything"])
        assert result.exit_code == 2
        assert new in result.output


class TestListPythonApis:
    def test_runs(self, runner):
        result = runner.invoke(audio, ["list-python-apis"])
        # May exit 0 (introspect available) or fall back to local stub — both ok.
        assert result.exit_code == 0
        # Should mention scitex_audio somewhere
        assert (
            "scitex_audio" in result.output.lower()
            or "scitex-audio" in result.output.lower()
        )


# EOF
