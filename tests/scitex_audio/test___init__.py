#!/usr/bin/env python3
"""Tests for scitex_audio package-level public API.

Currently covers ``announce_context`` — the orientation helper that
both backs the ``audio_announce_context`` MCP tool and is a public
Python API. No mocks: ``branch_resolver`` and ``speak_fn`` are
injectable seams; tests pass small hand-rolled fakes.
"""

import scitex_audio


def test_announce_context_includes_branch_when_resolver_returns_one():
    # Arrange
    spoken = []
    # Act
    result = scitex_audio.announce_context(
        branch_resolver=lambda cwd: "develop",
        speak_fn=lambda text: spoken.append(text),
    )
    # Assert
    assert "on branch develop" in result["announced_text"]


def test_announce_context_omits_branch_when_resolver_returns_none():
    # Arrange
    fake_speak = lambda text: None
    # Act
    result = scitex_audio.announce_context(
        branch_resolver=lambda cwd: None, speak_fn=fake_speak
    )
    # Assert
    assert "branch" not in result["announced_text"]


def test_announce_context_speaks_when_speak_aloud_true():
    # Arrange
    spoken = []
    # Act
    scitex_audio.announce_context(
        branch_resolver=lambda cwd: None,
        speak_fn=lambda text: spoken.append(text),
        speak_aloud=True,
    )
    # Assert
    assert len(spoken) == 1


def test_announce_context_skips_speaking_when_speak_aloud_false():
    # Arrange
    spoken = []
    # Act
    result = scitex_audio.announce_context(
        branch_resolver=lambda cwd: None,
        speak_fn=lambda text: spoken.append(text),
        speak_aloud=False,
    )
    # Assert
    assert result["spoke"] is False


def test_announce_context_reports_directory_name_in_result():
    # Arrange
    import os

    expected = os.path.basename(os.getcwd())
    # Act
    result = scitex_audio.announce_context(
        branch_resolver=lambda cwd: None, speak_aloud=False
    )
    # Assert
    assert result["directory_name"] == expected
