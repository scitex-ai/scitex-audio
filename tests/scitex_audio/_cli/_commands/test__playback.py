#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._playback."""

import click
import pytest

from scitex_audio._cli._commands._playback import register


class TestRegister:
    def test_register_attaches_stop_playback(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "stop-playback" in group.commands

    def test_register_attaches_relay(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "relay" in group.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
