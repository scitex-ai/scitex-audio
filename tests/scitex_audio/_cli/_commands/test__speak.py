#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._speak."""

import click
import pytest

from scitex_audio._cli._commands._speak import build_speak_kwargs, register


class TestBuildSpeakKwargs:
    def test_text_is_required_field(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["text"] == "hi"

    def test_play_true_by_default(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["play"] is True

    def test_no_play_disables_play(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, True, None, None, False)
        # Assert
        assert kwargs["play"] is False

    def test_fallback_true_by_default(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, None, False)
        # Assert
        assert kwargs["fallback"] is True

    def test_no_fallback_disables_fallback(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, None, True)
        # Assert
        assert kwargs["fallback"] is False

    def test_backend_included_when_set(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", "gtts", None, None, False, None, None, False)
        # Assert
        assert kwargs["backend"] == "gtts"

    def test_backend_absent_when_unset(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, None, False)
        # Assert
        assert "backend" not in kwargs

    def test_voice_included_when_set(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, "en", None, False, None, None, False)
        # Assert
        assert kwargs["voice"] == "en"

    def test_output_maps_to_output_path(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs(
            "hi", None, None, "/tmp/o.mp3", False, None, None, False
        )
        # Assert
        assert kwargs["output_path"] == "/tmp/o.mp3"

    def test_rate_included_when_set(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, 200, None, False)
        # Assert
        assert kwargs["rate"] == 200

    def test_speed_included_when_set(self):
        # Arrange
        # Act
        kwargs = build_speak_kwargs("hi", None, None, None, False, None, 1.5, False)
        # Assert
        assert kwargs["speed"] == 1.5


class TestRegister:
    def test_register_attaches_speak_text_command(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "speak-text" in group.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
