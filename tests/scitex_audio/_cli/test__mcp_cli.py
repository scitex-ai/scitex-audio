#!/usr/bin/env python3
"""Tests for scitex_audio._cli._mcp_cli (MCP subcommand group)."""

import pytest
from click.testing import CliRunner

from scitex_audio._cli._main import audio
from scitex_audio._cli._mcp_cli import mcp


@pytest.fixture
def runner():
    return CliRunner()


class TestMcpGroup:
    def test_help(self, runner):
        result = runner.invoke(mcp, ["--help"])
        assert result.exit_code == 0
        assert "MCP" in result.output

    def test_no_args_shows_help(self, runner):
        result = runner.invoke(mcp, [])
        assert result.exit_code == 0
        # Should list at least the canonical subcommands
        assert "start" in result.output
        assert "doctor" in result.output

    def test_json_lists_commands(self, runner):
        result = runner.invoke(mcp, ["--json"])
        assert result.exit_code == 0
        assert "start" in result.output


class TestMcpStart:
    def test_dry_run(self, runner):
        result = runner.invoke(mcp, ["start", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "stdio" in result.output

    def test_dry_run_http_transport(self, runner):
        result = runner.invoke(
            mcp, ["start", "-t", "http", "--port", "31999", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "http" in result.output
        assert "31999" in result.output

    def test_invalid_transport_rejected(self, runner):
        result = runner.invoke(mcp, ["start", "-t", "carrier-pigeon"])
        assert result.exit_code != 0


class TestMcpDoctor:
    def test_runs(self, runner):
        # doctor only checks imports — should be safe everywhere
        result = runner.invoke(mcp, ["doctor"])
        assert result.exit_code == 0
        assert "Health Check" in result.output


class TestMcpListTools:
    def test_text_output(self, runner):
        result = runner.invoke(mcp, ["list-tools"])
        assert result.exit_code == 0
        # At least one MCP tool name should appear in either fallback or main path
        assert "speak" in result.output.lower() or "audio" in result.output.lower()

    def test_json_output(self, runner):
        result = runner.invoke(mcp, ["list-tools", "--json"])
        assert result.exit_code == 0
        # JSON payload should mention "tools" or a known tool name
        assert "tools" in result.output or "speak" in result.output


class TestInstall:
    def test_text(self, runner):
        result = runner.invoke(mcp, ["install"])
        assert result.exit_code == 0
        assert "scitex-audio" in result.output
        assert "mcpServers" in result.output

    def test_json(self, runner):
        result = runner.invoke(mcp, ["install", "--json"])
        assert result.exit_code == 0
        assert "mcpServers" in result.output

    def test_old_installation_command_redirects(self, runner):
        result = runner.invoke(mcp, ["installation"])
        assert result.exit_code == 2
        assert "install" in result.output


class TestMcpThroughRootGroup:
    """Verify the MCP subgroup is wired into the root `audio` group."""

    def test_root_help_lists_mcp(self, runner):
        result = runner.invoke(audio, ["--help"])
        assert result.exit_code == 0
        assert "mcp" in result.output

    def test_root_can_invoke_mcp_subcommand(self, runner):
        result = runner.invoke(audio, ["mcp", "doctor"])
        assert result.exit_code == 0


# EOF
