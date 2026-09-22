#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke: `scitex-audio` CLI happy-paths (fast, offline, <60s each)."""

import shutil
import subprocess

import pytest

pytestmark = pytest.mark.smoke

_found = shutil.which("scitex-audio")
if _found is None:
    pytest.skip("scitex-audio console script not installed", allow_module_level=True)
CLI = str(_found)


def _run(*args):
    return subprocess.run(
        [CLI, *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_help_exits_zero():
    # Arrange
    # Act
    result = _run("--help")
    # Assert
    assert result.returncode == 0


def test_help_lists_speak_text_command():
    # Arrange
    # Act
    result = _run("--help")
    # Assert
    assert "speak-text" in result.stdout


def test_version_exits_zero():
    # Arrange
    # Act
    result = _run("--version")
    # Assert
    assert result.returncode == 0


def test_list_backends_exits_zero():
    # Arrange
    # Act
    result = _run("list-backends")
    # Assert
    assert result.returncode == 0


def test_list_backends_names_fallback_order():
    # Arrange
    # Act
    result = _run("list-backends")
    # Assert
    assert "elevenlabs" in result.stdout


def test_skills_list_exits_zero():
    # Arrange
    # Act
    result = _run("skills", "list")
    # Assert
    assert result.returncode == 0


def test_system_deps_list_names_apt_packages():
    # Arrange
    # Act
    result = _run("dev", "system-deps", "list")
    # Assert
    assert "ffmpeg" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
