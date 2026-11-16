"""Real filesystem checks and opt-in native whisper.cpp recognition controls."""

import json
import os
from pathlib import Path
import sys
import shutil
import subprocess

import pytest

from scitex_audio._stt import find_whisper_cli, find_whisper_model


@pytest.fixture(autouse=True)
def restore_stt_environment():
    keys = ("SCITEX_AUDIO_WHISPER_CLI", "SCITEX_AUDIO_WHISPER_MODEL")
    previous = {key: os.environ.get(key) for key in keys}
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_non_executable_cli_override_is_rejected(tmp_path):
    # Arrange
    path = tmp_path / "not-executable"
    path.write_text("owned filesystem fixture; never executed")
    path.chmod(0o600)
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = str(path)
    # Act
    found = find_whisper_cli()
    # Assert
    assert found is None


def test_missing_cli_override_does_not_silently_select_another_binary(tmp_path):
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = str(tmp_path / "missing")
    # Act
    found = find_whisper_cli()
    # Assert
    assert found is None


def test_executable_file_override_is_honored_without_execution():
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_CLI"] = sys.executable
    # Act
    found = find_whisper_cli()
    # Assert
    assert found == sys.executable


def test_model_override_is_a_file_path_not_a_model_name(tmp_path):
    # Arrange
    path = tmp_path / "owned-model-path.bin"
    path.write_bytes(b"")  # Discovery fixture only, not usable recognition weights.
    os.environ["SCITEX_AUDIO_WHISPER_MODEL"] = str(path)
    # Act
    found = find_whisper_model("tiny")
    # Assert
    assert found == str(path)


def test_missing_model_override_is_reported_missing(tmp_path):
    # Arrange
    os.environ["SCITEX_AUDIO_WHISPER_MODEL"] = str(tmp_path / "missing.bin")
    # Act
    found = find_whisper_model()
    # Assert
    assert found is None


@pytest.fixture(params=[None, "auto"])
def native_auto_result(request, tmp_path):
    """Opt in with RUN_STT_NATIVE=1 and STT_TEST_SAMPLE=upstream samples/jfk.wav.

    Configure real binary/model paths with SCITEX_AUDIO_WHISPER_CLI/MODEL.
    Linux strace observes the real recognizer externally; no commands or
    results are replaced. Tests never download assets. Selecting an incomplete
    native profile fails; default CI retains explicit native-asset skips.
    """
    if os.environ.get("RUN_STT_NATIVE") != "1":
        pytest.skip("Native STT profile not selected; requires real whisper.cpp/model/JFK fixture")
    sample = os.environ.get("STT_TEST_SAMPLE")
    cli, model = find_whisper_cli(), find_whisper_model("tiny")
    tracer = shutil.which("strace")
    if not sample or not Path(sample).is_file() or not cli or not model or not tracer:
        pytest.fail("Native STT profile selected but binary, model, JFK fixture or strace is missing")
    trace = tmp_path / "recognizer.trace"
    code = (
        "import json,sys; from scitex_audio._stt import transcribe; "
        "result=transcribe(sys.argv[1],language=json.loads(sys.argv[2]),"
        "whisper_cli=sys.argv[3],model_path=sys.argv[4]); print(json.dumps(result))"
    )
    child_env = {
        key: os.environ[key]
        for key in ("PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "SYSTEMROOT")
        if key in os.environ
    }
    child_env.update(HOME=str(tmp_path), TMPDIR=str(tmp_path))
    completed = subprocess.run(
        [tracer, "-f", "-s", "8192", "-e", "trace=execve,write", "-o", str(trace),
         sys.executable, "-c", code, sample, json.dumps(request.param), cli, model],
        capture_output=True, text=True, env=child_env, timeout=180,
    )
    if completed.returncode:
        pytest.fail("Native trace failed: " + completed.stderr[-2000:])
    result = json.loads(completed.stdout)
    if not result.get("success"):
        pytest.fail(result.get("error", "native transcription failed"))
    native_trace = trace.read_text()
    (tmp_path / "native-stt.json").write_text(json.dumps({
        "language_requested": request.param, "binary": cli, "model": model,
        "result": result, "trace": str(trace),
    }, indent=2))
    yield result, native_trace


def test_native_auto_mode_performs_language_detection(native_auto_result):
    # Arrange
    _, native_trace = native_auto_result
    # Act
    stderr = native_trace.lower()
    # Assert
    assert "auto-detected language" in stderr


def test_native_auto_mode_transcribes_upstream_jfk_sample(native_auto_result):
    # Arrange
    result, _ = native_auto_result
    expected = ["fellow americans", "your country"]
    # Act
    transcript = result["text"].lower()
    # Assert
    assert all(fragment in transcript for fragment in expected)
