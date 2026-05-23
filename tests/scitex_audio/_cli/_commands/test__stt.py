#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._stt."""

import click
import pytest

from scitex_audio._cli._commands._stt import register


class TestRegister:
    def test_register_attaches_transcribe_audio(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "transcribe-audio" in group.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
