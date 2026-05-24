#!/usr/bin/env python3
"""Tests for scitex_audio._mcp.server_tools (FastMCP tool bodies).

No mocks: every tool body exposes injectable seams
(``available_fn=`` / ``fallback_order=`` / ``status_fn=`` / ``check_fn=``
/ ``stop_fn=`` / ``generate_fn=`` / ``audio_dir=`` / ``announce_fn=``).
Tests pass small hand-rolled fakes and real ``tmp_path`` directories;
each tool returns a JSON-string envelope that the test parses and
asserts on.
"""

import json

from scitex_audio._mcp import server_tools as st


# --------------------------------------------------------------------------- #
# available_backends_tool                                                     #
# --------------------------------------------------------------------------- #
def test_available_backends_tool_reports_injected_backends():
    # Arrange
    fake_available = lambda: ["gtts", "pyttsx3"]
    fallback = ["elevenlabs", "luxtts", "gtts", "pyttsx3"]
    # Act
    payload = json.loads(
        st.available_backends_tool(available_fn=fake_available, fallback_order=fallback)
    )
    # Assert
    assert payload["available"] == ["gtts", "pyttsx3"]


def test_available_backends_tool_echoes_injected_fallback_order():
    # Arrange
    fallback = ["elevenlabs", "gtts"]
    # Act
    payload = json.loads(
        st.available_backends_tool(available_fn=lambda: [], fallback_order=fallback)
    )
    # Assert
    assert payload["fallback_order"] == ["elevenlabs", "gtts"]


def test_available_backends_tool_returns_error_envelope_on_failure():
    # Arrange
    def boom():
        raise RuntimeError("backend probe failed")

    # Act
    payload = json.loads(
        st.available_backends_tool(available_fn=boom, fallback_order=["gtts"])
    )
    # Assert
    assert payload["success"] is False


# --------------------------------------------------------------------------- #
# check_wsl_audio_tool                                                        #
# --------------------------------------------------------------------------- #
def test_check_wsl_audio_tool_passes_through_status_dict():
    # Arrange
    fake_status = lambda: {"is_wsl": True, "recommended": "windows"}
    # Act
    payload = json.loads(st.check_wsl_audio_tool(status_fn=fake_status))
    # Assert
    assert payload["recommended"] == "windows"


def test_check_wsl_audio_tool_marks_success_true():
    # Arrange
    fake_status = lambda: {"is_wsl": False}
    # Act
    payload = json.loads(st.check_wsl_audio_tool(status_fn=fake_status))
    # Assert
    assert payload["success"] is True


# --------------------------------------------------------------------------- #
# check_local_audio_available_tool                                            #
# --------------------------------------------------------------------------- #
def test_check_local_audio_available_tool_reports_sink_state():
    # Arrange
    fake_check = lambda: {"available": True, "state": "RUNNING"}
    # Act
    payload = json.loads(st.check_local_audio_available_tool(check_fn=fake_check))
    # Assert
    assert payload["state"] == "RUNNING"


def test_check_local_audio_available_tool_returns_error_envelope_on_failure():
    # Arrange
    def boom():
        raise OSError("pactl missing")

    # Act
    payload = json.loads(st.check_local_audio_available_tool(check_fn=boom))
    # Assert
    assert payload["success"] is False


# --------------------------------------------------------------------------- #
# stop_speech_tool                                                            #
# --------------------------------------------------------------------------- #
def test_stop_speech_tool_invokes_injected_stopper_once():
    # Arrange
    calls = []
    # Act
    st.stop_speech_tool(stop_fn=lambda: calls.append("stop"))
    # Assert
    assert calls == ["stop"]


def test_stop_speech_tool_confirms_stopped_in_envelope():
    # Arrange
    fake_stop = lambda: None
    # Act
    payload = json.loads(st.stop_speech_tool(stop_fn=fake_stop))
    # Assert
    assert payload["stopped"] is True


# --------------------------------------------------------------------------- #
# generate_bytes_tool                                                         #
# --------------------------------------------------------------------------- #
def test_generate_bytes_tool_writes_audio_to_explicit_path(tmp_path):
    # Arrange
    target = tmp_path / "out.mp3"
    fake_generate = lambda text, backend=None, voice=None: b"ID3-fake-bytes"
    # Act
    st.generate_bytes_tool("hello", output_path=str(target), generate_fn=fake_generate)
    # Assert
    assert target.read_bytes() == b"ID3-fake-bytes"


def test_generate_bytes_tool_reports_written_byte_count(tmp_path):
    # Arrange
    target = tmp_path / "out.mp3"
    fake_generate = lambda text, backend=None, voice=None: b"abcd"
    # Act
    payload = json.loads(
        st.generate_bytes_tool("hi", output_path=str(target), generate_fn=fake_generate)
    )
    # Assert
    assert payload["bytes"] == 4


def test_generate_bytes_tool_uses_injected_audio_dir_when_no_path(tmp_path):
    # Arrange
    fake_generate = lambda text, backend=None, voice=None: b"xy"
    # Act
    payload = json.loads(
        st.generate_bytes_tool("hi", audio_dir=tmp_path, generate_fn=fake_generate)
    )
    # Assert
    assert payload["path"].startswith(str(tmp_path))


def test_generate_bytes_tool_returns_error_envelope_on_failure(tmp_path):
    # Arrange
    def boom(text, backend=None, voice=None):
        raise ValueError("no backend")

    # Act
    payload = json.loads(
        st.generate_bytes_tool(
            "hi", output_path=str(tmp_path / "x.mp3"), generate_fn=boom
        )
    )
    # Assert
    assert payload["success"] is False


# --------------------------------------------------------------------------- #
# announce_context_tool                                                       #
# --------------------------------------------------------------------------- #
def test_announce_context_tool_passes_through_announce_result():
    # Arrange
    fake_announce = lambda include_full_path=False: {
        "directory_name": "myproj",
        "git_branch": "develop",
        "announced_text": "Working in myproj, on branch develop",
        "spoke": True,
    }
    # Act
    payload = json.loads(st.announce_context_tool(announce_fn=fake_announce))
    # Assert
    assert payload["announced_text"] == "Working in myproj, on branch develop"


def test_announce_context_tool_forwards_include_full_path_flag():
    # Arrange
    seen = {}

    def fake_announce(include_full_path=False):
        seen["flag"] = include_full_path
        return {"directory_name": "x"}

    # Act
    st.announce_context_tool(include_full_path=True, announce_fn=fake_announce)
    # Assert
    assert seen["flag"] is True


def test_announce_context_tool_returns_error_envelope_on_failure():
    # Arrange
    def boom(include_full_path=False):
        raise RuntimeError("git failed")

    # Act
    payload = json.loads(st.announce_context_tool(announce_fn=boom))
    # Assert
    assert payload["success"] is False
