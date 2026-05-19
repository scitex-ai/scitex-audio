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
    def test_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_help_text_to_speech_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "Text-to-speech" in result.output

    def test_help_config_yaml_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "config.yaml" in result.output

    def test_help_scitex_audio_config_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "SCITEX_AUDIO_CONFIG" in result.output


    def test_version_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_version_scitex_audio_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Act
        # Assert
        assert "scitex-audio" in result.output


    def test_short_version_flag_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["-V"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_short_version_flag_scitex_audio_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["-V"])
        # Act
        # Assert
        assert "scitex-audio" in result.output


    def test_no_args_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help_speak_in_result_output_lower(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Act
        # Assert
        assert "speak" in result.output.lower()


    def test_help_recursive_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_speak_text_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Act
        # Assert
        assert "speak-text" in result.output

    def test_help_recursive_list_backends_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Act
        # Assert
        assert "list-backends" in result.output


    def test_root_json_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_root_json_speak_text_in_result_output_or_list_backends_in_result_outpu(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Act
        # Assert
        assert "speak-text" in result.output or "list-backends" in result.output



class TestSpeakText:
    def test_speak_text_calls_backend_kwargs_text_hello(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello"])
        mock_speak.assert_called_once()
        # Act
        kwargs = mock_speak.call_args[1]
        # Act
        # Assert
        assert kwargs["text"] == "Hello"

    def test_speak_text_calls_backend_kwargs_play_is_true(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello"])
        mock_speak.assert_called_once()
        # Act
        kwargs = mock_speak.call_args[1]
        # Act
        # Assert
        assert kwargs["play"] is True

    def test_speak_text_calls_backend_kwargs_fallback_is_true(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})
        with patch("scitex_audio.speak", mock_speak):
            result = runner.invoke(audio, ["speak-text", "Hello"])
        mock_speak.assert_called_once()
        # Act
        kwargs = mock_speak.call_args[1]
        # Act
        # Assert
        assert kwargs["fallback"] is True


    def test_speak_text_backend_option(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})
        # Act
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "-b", "gtts"])
        # Assert
        assert mock_speak.call_args[1]["backend"] == "gtts"

    def test_speak_text_invalid_backend_rejected(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hi", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0

    def test_speak_text_no_play_flag(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={})
        # Act
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "--no-play"])
        # Assert
        assert mock_speak.call_args[1]["play"] is False

    def test_speak_text_no_fallback_flag(self, runner):
        # Arrange
        mock_speak = MagicMock(return_value={"played": True})
        # Act
        with patch("scitex_audio.speak", mock_speak):
            runner.invoke(audio, ["speak-text", "Hi", "--no-fallback"])
        # Assert
        assert mock_speak.call_args[1]["fallback"] is False


class TestListBackends:
    def test_text_output_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_avail = MagicMock(return_value=["gtts"])
        # Act
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_text_output_available_in_result_output_lower(self, runner):
        # Arrange
        mock_avail = MagicMock(return_value=["gtts"])
        # Act
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends"])
        # Act
        # Assert
        assert "available" in result.output.lower()


    def test_json_envelope_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_avail = MagicMock(return_value=["gtts", "pyttsx3"])
        # Act
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends", "--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_json_envelope_available_in_result_output(self, runner):
        # Arrange
        mock_avail = MagicMock(return_value=["gtts", "pyttsx3"])
        # Act
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends", "--json"])
        # Act
        # Assert
        assert "available" in result.output

    def test_json_envelope_fallback_order_in_result_output(self, runner):
        # Arrange
        mock_avail = MagicMock(return_value=["gtts", "pyttsx3"])
        # Act
        with (
            patch("scitex_audio.available_backends", mock_avail),
            patch(
                "scitex_audio.FALLBACK_ORDER",
                ["pyttsx3", "gtts", "luxtts", "elevenlabs"],
            ),
        ):
            result = runner.invoke(audio, ["list-backends", "--json"])
        # Act
        # Assert
        assert "fallback_order" in result.output



class TestCheckBackends:
    def test_runs_text_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_status = {
            "is_wsl": False,
            "wslg_available": False,
            "pulse_server_exists": False,
            "pulse_connected": False,
            "windows_fallback_available": False,
            "recommended": "linux",
        }
        # Act
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_runs_text_audio_status_check_in_result_output(self, runner):
        # Arrange
        mock_status = {
            "is_wsl": False,
            "wslg_available": False,
            "pulse_server_exists": False,
            "pulse_connected": False,
            "windows_fallback_available": False,
            "recommended": "linux",
        }
        # Act
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends"])
        # Act
        # Assert
        assert "Audio Status Check" in result.output


    def test_runs_json_result_exit_code_equals_n_0(self, runner):
        # Arrange
        mock_status = {
            "is_wsl": True,
            "wslg_available": True,
            "pulse_server_exists": True,
            "pulse_connected": True,
            "windows_fallback_available": True,
            "recommended": "linux",
        }
        # Act
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends", "--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_runs_json_is_wsl_in_result_output(self, runner):
        # Arrange
        mock_status = {
            "is_wsl": True,
            "wslg_available": True,
            "pulse_server_exists": True,
            "pulse_connected": True,
            "windows_fallback_available": True,
            "recommended": "linux",
        }
        # Act
        with patch("scitex_audio.check_wsl_audio", return_value=mock_status):
            result = runner.invoke(audio, ["check-backends", "--json"])
        # Act
        # Assert
        assert "is_wsl" in result.output



class TestStopPlayback:
    def test_dry_run_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_dry_run_dry_run_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Act
        # Assert
        assert "DRY RUN" in result.output


    def test_calls_stop_speech(self, runner):
        # Arrange
        mock_stop = MagicMock()
        # Act
        with patch("scitex_audio.stop_speech", mock_stop):
            result = runner.invoke(audio, ["stop-playback"])
        # Assert
        assert result.exit_code == 0
        mock_stop.assert_called_once()


class TestTranscribeAudio:
    def test_calls_transcribe_result_exit_code_equals_n_0(self, runner, tmp_path):
        # transcribe-audio takes a Click Path(exists=True), so we need a real file
        # Arrange
        audio_file = tmp_path / "x.wav"
        audio_file.write_bytes(b"")
        mock_transcribe = MagicMock(return_value={"success": True, "text": "hello"})
        # Act
        with patch("scitex_audio.transcribe", mock_transcribe):
            result = runner.invoke(audio, ["transcribe-audio", str(audio_file)])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_calls_transcribe_hello_in_result_output(self, runner, tmp_path):
        # transcribe-audio takes a Click Path(exists=True), so we need a real file
        # Arrange
        audio_file = tmp_path / "x.wav"
        audio_file.write_bytes(b"")
        mock_transcribe = MagicMock(return_value={"success": True, "text": "hello"})
        # Act
        with patch("scitex_audio.transcribe", mock_transcribe):
            result = runner.invoke(audio, ["transcribe-audio", str(audio_file)])
        # Act
        # Assert
        assert "hello" in result.output



class TestShowEnvTemplate:
    def test_stdout_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_stdout_len_result_output_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Act
        # Assert
        assert len(result.output) > 0


    def test_no_sensitive_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template", "--no-sensitive"])
        # Assert
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
    def test_old_command_exits_with_hint_result_exit_code_equals_n_2(self, runner, old, new):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
        # Act
        # Assert
        assert result.exit_code == 2

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
    def test_old_command_exits_with_hint_new_in_result_output(self, runner, old, new):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
        # Act
        # Assert
        assert new in result.output



class TestListPythonApis:
    def test_runs_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_runs_scitex_audio_in_result_output_lower_or_scitex_audio_in_resul(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Act
        # Assert
        assert (
            "scitex_audio" in result.output.lower()
            or "scitex-audio" in result.output.lower()
        )



# EOF
