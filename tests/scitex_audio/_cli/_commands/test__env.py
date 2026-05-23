#!/usr/bin/env python3
"""Tests for scitex_audio._cli._commands._env."""

import click
import pytest

from scitex_audio._cli._commands._env import register


class TestRegister:
    def test_register_attaches_show_env_template(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "show-env-template" in group.commands

    def test_register_attaches_list_python_apis(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "list-python-apis" in group.commands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
