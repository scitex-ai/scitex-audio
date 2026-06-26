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
    def test_register_attaches_dev_group(self):
        group = _build_group()
        assert "dev" in group.commands

    def test_dev_has_system_deps_subgroup(self):
        group = _build_group()
        dev = group.commands["dev"]
        assert "system-deps" in dev.commands

    def test_system_deps_has_list_and_install(self):
        group = _build_group()
        system_deps = group.commands["dev"].commands["system-deps"]
        assert {"list", "install"} <= set(system_deps.commands)


class TestList:
    def test_list_prints_apt_names_one_per_line(self):
        result = CliRunner().invoke(_build_group(), ["dev", "system-deps", "list"])
        assert result.exit_code == 0
        lines = result.output.split()
        assert "ffmpeg" in lines
        assert "portaudio19-dev" in lines

    def test_list_json(self):
        result = CliRunner().invoke(
            _build_group(), ["dev", "system-deps", "list", "--json"]
        )
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert {row["package"] for row in payload} == {"ffmpeg", "portaudio19-dev"}
        assert all(row["provider"] == "scitex-audio" for row in payload)


class TestInstall:
    def test_install_defaults_to_dry_run(self):
        result = CliRunner().invoke(_build_group(), ["dev", "system-deps", "install"])
        assert result.exit_code == 0
        assert "dry-run" in result.output
        assert "apt-get install" in result.output
        assert "ffmpeg" in result.output
        assert "portaudio19-dev" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
