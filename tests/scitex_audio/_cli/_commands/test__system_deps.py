#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._cli._commands._system_deps."""

import json

import click
import pytest
from click.testing import CliRunner

from scitex_audio._cli._commands._system_deps import register


def _build_group():
    group = click.Group()
    register(group)
    return group


class TestRegister:
    def test_register_attaches_dev_command_group(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "dev" in group.commands

    def test_dev_exposes_system_deps_subgroup(self):
        # Arrange
        group = click.Group()
        # Act
        register(group)
        # Assert
        assert "system-deps" in group.commands["dev"].commands

    def test_system_deps_group_has_list_verb(self):
        # Arrange
        group = _build_group()
        # Act
        verbs = set(group.commands["dev"].commands["system-deps"].commands)
        # Assert
        assert "list" in verbs

    def test_system_deps_group_has_install_verb(self):
        # Arrange
        group = _build_group()
        # Act
        verbs = set(group.commands["dev"].commands["system-deps"].commands)
        # Assert
        assert "install" in verbs


class TestListVerb:
    def test_list_outputs_ffmpeg_package_name(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "list"])
        # Assert
        assert "ffmpeg" in result.output.split()

    def test_list_outputs_portaudio_package_name(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "list"])
        # Assert
        assert "portaudio19-dev" in result.output.split()

    def test_list_exits_zero_on_success(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "list"])
        # Assert
        assert result.exit_code == 0

    def test_list_json_emits_both_apt_packages(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(
            _build_group(), ["dev", "system-deps", "list", "--json"]
        )
        # Assert
        assert {row["package"] for row in json.loads(result.output)} == {
            "ffmpeg",
            "portaudio19-dev",
        }

    def test_list_json_tags_provider_as_scitex_audio(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(
            _build_group(), ["dev", "system-deps", "list", "--json"]
        )
        # Assert
        assert all(
            row["provider"] == "scitex-audio" for row in json.loads(result.output)
        )


class TestInstallVerb:
    def test_install_defaults_to_dry_run_preview(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "install"])
        # Assert
        assert "dry-run" in result.output

    def test_install_dry_run_previews_apt_install(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "install"])
        # Assert
        assert "apt-get install" in result.output

    def test_install_dry_run_includes_declared_packages(self):
        # Arrange
        runner = CliRunner()
        # Act
        result = runner.invoke(_build_group(), ["dev", "system-deps", "install"])
        # Assert
        assert "ffmpeg" in result.output and "portaudio19-dev" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
