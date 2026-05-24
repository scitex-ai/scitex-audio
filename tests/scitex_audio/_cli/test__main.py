#!/usr/bin/env python3
"""Tests for scitex_audio._cli._main (Click root group + leaf commands).

Covers the surface area of the `scitex-audio` CLI:
  - root help, --version, --help-recursive, --json
  - speak-text option plumbing (real attribute swap on scitex_audio.speak)
  - list-backends rendering (text + --json)
  - check-backends, stop-playback dry-run, transcribe-audio,
    show-env-template
  - deprecated redirects exit non-zero with hint
  - list-python-apis runs end-to-end

Backend calls that would need network / hardware are intercepted by
swapping the real `scitex_audio.<name>` attribute with a hand-rolled
recorder via a yield-based fixture (no `unittest.mock`).
"""

import pytest
from click.testing import CliRunner

import scitex_audio
from scitex_audio._cli._main import audio


class _CallRecorder:
    """Callable that records each call's args/kwargs and returns a value."""

    def __init__(self, return_value=None) -> None:
        self.calls: list[tuple] = []
        self.return_value = return_value

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.return_value


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def fake_speak():
    """Swap `scitex_audio.speak` with a recorder; restore on teardown."""
    recorder = _CallRecorder(return_value={"played": True})
    real = scitex_audio.speak
    scitex_audio.speak = recorder
    try:
        yield recorder
    finally:
        scitex_audio.speak = real


@pytest.fixture
def fake_backends_single_gtts():
    """`available_backends() == ["gtts"]` plus a known FALLBACK_ORDER."""
    real_avail = scitex_audio.available_backends
    real_order = scitex_audio.FALLBACK_ORDER
    scitex_audio.available_backends = lambda: ["gtts"]
    scitex_audio.FALLBACK_ORDER = ["pyttsx3", "gtts", "luxtts", "elevenlabs"]
    try:
        yield
    finally:
        scitex_audio.available_backends = real_avail
        scitex_audio.FALLBACK_ORDER = real_order


@pytest.fixture
def fake_backends_two():
    """`available_backends() == ["gtts", "pyttsx3"]`."""
    real_avail = scitex_audio.available_backends
    real_order = scitex_audio.FALLBACK_ORDER
    scitex_audio.available_backends = lambda: ["gtts", "pyttsx3"]
    scitex_audio.FALLBACK_ORDER = ["pyttsx3", "gtts", "luxtts", "elevenlabs"]
    try:
        yield
    finally:
        scitex_audio.available_backends = real_avail
        scitex_audio.FALLBACK_ORDER = real_order


@pytest.fixture
def fake_check_wsl_audio_linux():
    recorder = _CallRecorder(
        return_value={
            "is_wsl": False,
            "wslg_available": False,
            "pulse_server_exists": False,
            "pulse_connected": False,
            "windows_fallback_available": False,
            "recommended": "linux",
        }
    )
    real = scitex_audio.check_wsl_audio
    scitex_audio.check_wsl_audio = recorder
    try:
        yield recorder
    finally:
        scitex_audio.check_wsl_audio = real


@pytest.fixture
def fake_check_wsl_audio_wsl():
    recorder = _CallRecorder(
        return_value={
            "is_wsl": True,
            "wslg_available": True,
            "pulse_server_exists": True,
            "pulse_connected": True,
            "windows_fallback_available": True,
            "recommended": "linux",
        }
    )
    real = scitex_audio.check_wsl_audio
    scitex_audio.check_wsl_audio = recorder
    try:
        yield recorder
    finally:
        scitex_audio.check_wsl_audio = real


@pytest.fixture
def fake_stop_speech():
    recorder = _CallRecorder(return_value=None)
    real = scitex_audio.stop_speech
    scitex_audio.stop_speech = recorder
    try:
        yield recorder
    finally:
        scitex_audio.stop_speech = real


@pytest.fixture
def fake_transcribe():
    recorder = _CallRecorder(return_value={"success": True, "text": "hello"})
    real = scitex_audio.transcribe
    scitex_audio.transcribe = recorder
    try:
        yield recorder
    finally:
        scitex_audio.transcribe = real


class TestRootGroup:
    def test_help_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_help_output_mentions_text_to_speech(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "Text-to-speech" in result.output

    def test_help_output_mentions_config_yaml(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "config.yaml" in result.output

    def test_help_output_mentions_scitex_audio_config_env(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Assert
        assert "SCITEX_AUDIO_CONFIG" in result.output

    def test_version_flag_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Assert
        assert result.exit_code == 0

    def test_version_flag_output_mentions_scitex_audio(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--version"])
        # Assert
        assert "scitex-audio" in result.output

    def test_short_version_flag_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["-V"])
        # Assert
        assert result.exit_code == 0

    def test_short_version_flag_output_mentions_scitex_audio(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["-V"])
        # Assert
        assert "scitex-audio" in result.output

    def test_no_args_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert result.exit_code == 0

    def test_no_args_output_mentions_speak(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, [])
        # Assert
        assert "speak" in result.output.lower()

    def test_help_recursive_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_output_mentions_speak_text(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "speak-text" in result.output

    def test_help_recursive_output_mentions_list_backends(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help-recursive"])
        # Assert
        assert "list-backends" in result.output

    def test_root_json_flag_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Assert
        assert result.exit_code == 0

    def test_root_json_flag_lists_one_of_known_subcommands(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["--json"])
        # Assert
        assert "speak-text" in result.output or "list-backends" in result.output


class TestSpeakText:
    def test_speak_text_threads_text_argument_into_kwargs(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello"])
        # Assert
        assert fake_speak.calls[0][1]["text"] == "Hello"

    def test_speak_text_default_play_kwarg_is_true(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello"])
        # Assert
        assert fake_speak.calls[0][1]["play"] is True

    def test_speak_text_default_fallback_kwarg_is_true(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hello"])
        # Assert
        assert fake_speak.calls[0][1]["fallback"] is True

    def test_speak_text_threads_backend_option_into_kwargs(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hi", "-b", "gtts"])
        # Assert
        assert fake_speak.calls[0][1]["backend"] == "gtts"

    def test_speak_text_invalid_backend_exits_nonzero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["speak-text", "Hi", "-b", "invalid"])
        # Assert
        assert result.exit_code != 0

    def test_speak_text_no_play_flag_threads_play_false(self, runner, fake_speak):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hi", "--no-play"])
        # Assert
        assert fake_speak.calls[0][1]["play"] is False

    def test_speak_text_no_fallback_flag_threads_fallback_false(
        self, runner, fake_speak
    ):
        # Arrange
        # Act
        runner.invoke(audio, ["speak-text", "Hi", "--no-fallback"])
        # Assert
        assert fake_speak.calls[0][1]["fallback"] is False


class TestListBackends:
    def test_text_output_exits_with_code_zero(self, runner, fake_backends_single_gtts):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert result.exit_code == 0

    def test_text_output_mentions_available(self, runner, fake_backends_single_gtts):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends"])
        # Assert
        assert "available" in result.output.lower()

    def test_json_envelope_exits_with_code_zero(self, runner, fake_backends_two):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert result.exit_code == 0

    def test_json_envelope_mentions_available_field(self, runner, fake_backends_two):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert "available" in result.output

    def test_json_envelope_mentions_fallback_order_field(
        self, runner, fake_backends_two
    ):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-backends", "--json"])
        # Assert
        assert "fallback_order" in result.output


class TestCheckBackends:
    def test_text_output_exits_with_code_zero(
        self, runner, fake_check_wsl_audio_linux
    ):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends"])
        # Assert
        assert result.exit_code == 0

    def test_text_output_mentions_status_header(
        self, runner, fake_check_wsl_audio_linux
    ):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends"])
        # Assert
        assert "Audio Status Check" in result.output

    def test_json_output_exits_with_code_zero(self, runner, fake_check_wsl_audio_wsl):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends", "--json"])
        # Assert
        assert result.exit_code == 0

    def test_json_output_mentions_is_wsl_field(self, runner, fake_check_wsl_audio_wsl):
        # Arrange
        # Act
        result = runner.invoke(audio, ["check-backends", "--json"])
        # Assert
        assert "is_wsl" in result.output


class TestStopPlayback:
    def test_dry_run_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Assert
        assert result.exit_code == 0

    def test_dry_run_output_mentions_dry_run_marker(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["stop-playback", "--dry-run"])
        # Assert
        assert "DRY RUN" in result.output

    def test_stop_playback_invokes_stop_speech_exactly_once(
        self, runner, fake_stop_speech
    ):
        # Arrange
        # Act
        runner.invoke(audio, ["stop-playback"])
        # Assert
        assert len(fake_stop_speech.calls) == 1


class TestTranscribeAudio:
    def test_transcribe_command_exits_with_code_zero(
        self, runner, tmp_path, fake_transcribe
    ):
        # Arrange
        audio_file = tmp_path / "x.wav"
        audio_file.write_bytes(b"")
        # Act
        result = runner.invoke(audio, ["transcribe-audio", str(audio_file)])
        # Assert
        assert result.exit_code == 0

    def test_transcribe_command_emits_recognised_text(
        self, runner, tmp_path, fake_transcribe
    ):
        # Arrange
        audio_file = tmp_path / "x.wav"
        audio_file.write_bytes(b"")
        # Act
        result = runner.invoke(audio, ["transcribe-audio", str(audio_file)])
        # Assert
        assert "hello" in result.output


class TestShowEnvTemplate:
    def test_default_stdout_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Assert
        assert result.exit_code == 0

    def test_default_stdout_emits_non_empty_payload(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["show-env-template"])
        # Assert
        assert len(result.output) > 0

    def test_no_sensitive_flag_exits_with_code_zero(self, runner):
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
    def test_old_command_exits_with_code_two(self, runner, old, new):
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
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
    def test_old_command_output_mentions_new_name(self, runner, old, new):
        # Arrange
        # Act
        result = runner.invoke(audio, [old, "anything"])
        # Assert
        assert new in result.output


class TestListPythonApis:
    def test_list_python_apis_exits_with_code_zero(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Assert
        assert result.exit_code == 0

    def test_list_python_apis_output_mentions_scitex_audio(self, runner):
        # Arrange
        # Act
        result = runner.invoke(audio, ["list-python-apis"])
        # Assert
        assert (
            "scitex_audio" in result.output.lower()
            or "scitex-audio" in result.output.lower()
        )


# EOF
