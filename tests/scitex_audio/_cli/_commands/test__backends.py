#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._backends."""

import click
import pytest

from scitex_audio._cli._commands._backends import register


class TestRegister:
    def test_register_attaches_list_backends(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "list-backends" in group.commands

    def test_register_attaches_check_backends(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "check-backends" in group.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
