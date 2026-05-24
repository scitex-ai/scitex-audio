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
    def test_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["--help"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_help_mcp_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["--help"])
        # Act
        # Assert
        assert "MCP" in result.output


    def test_no_args_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, [])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help_start_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, [])
        # Act
        # Assert
        assert "start" in result.output

    def test_no_args_shows_help_doctor_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, [])
        # Act
        # Assert
        assert "doctor" in result.output


    def test_json_lists_commands_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_json_lists_commands_start_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["--json"])
        # Act
        # Assert
        assert "start" in result.output



class TestMcpStart:
    def test_dry_run_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["start", "--dry-run"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_dry_run_dry_run_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["start", "--dry-run"])
        # Act
        # Assert
        assert "DRY RUN" in result.output

    def test_dry_run_stdio_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["start", "--dry-run"])
        # Act
        # Assert
        assert "stdio" in result.output


    def test_dry_run_http_transport_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(
            mcp, ["start", "-t", "http", "--port", "31999", "--dry-run"]
        )
        # Act
        # Assert
        assert result.exit_code == 0

    def test_dry_run_http_transport_http_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(
            mcp, ["start", "-t", "http", "--port", "31999", "--dry-run"]
        )
        # Act
        # Assert
        assert "http" in result.output

    def test_dry_run_http_transport_n_31999_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(
            mcp, ["start", "-t", "http", "--port", "31999", "--dry-run"]
        )
        # Act
        # Assert
        assert "31999" in result.output


    def test_invalid_transport_rejected(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["start", "-t", "carrier-pigeon"])
        # Assert
        assert result.exit_code != 0


class TestMcpDoctor:
    def test_runs_result_exit_code_equals_n_0(self, runner):
        # doctor only checks imports — should be safe everywhere
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["doctor"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_runs_health_check_in_result_output(self, runner):
        # doctor only checks imports — should be safe everywhere
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["doctor"])
        # Act
        # Assert
        assert "Health Check" in result.output



class TestMcpListTools:
    def test_text_output_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["list-tools"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_text_output_speak_in_result_output_lower_or_audio_in_result_output_lower(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["list-tools"])
        # Act
        # Assert
        assert "speak" in result.output.lower() or "audio" in result.output.lower()


    def test_json_output_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["list-tools", "--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_json_output_tools_in_result_output_or_speak_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["list-tools", "--json"])
        # Act
        # Assert
        assert "tools" in result.output or "speak" in result.output



class TestInstall:
    def test_text_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["install"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_text_scitex_audio_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["install"])
        # Act
        # Assert
        assert "scitex-audio" in result.output

    def test_text_mcpservers_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["install"])
        # Act
        # Assert
        assert "mcpServers" in result.output


    def test_json_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["install", "--json"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_json_mcpservers_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["install", "--json"])
        # Act
        # Assert
        assert "mcpServers" in result.output


    def test_old_installation_command_redirects_result_exit_code_equals_n_2(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["installation"])
        # Act
        # Assert
        assert result.exit_code == 2

    def test_old_installation_command_redirects_install_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(mcp, ["installation"])
        # Act
        # Assert
        assert "install" in result.output



class TestMcpThroughRootGroup:
    """Verify the MCP subgroup is wired into the root `audio` group."""

    def test_root_help_lists_mcp_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert result.exit_code == 0

    def test_root_help_lists_mcp_mcp_in_result_output(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["--help"])
        # Act
        # Assert
        assert "mcp" in result.output


    def test_root_can_invoke_mcp_subcommand(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        result = runner.invoke(audio, ["mcp", "doctor"])
        # Assert
        assert result.exit_code == 0


# EOF
