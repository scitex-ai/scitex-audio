#!/usr/bin/env python3
"""MCP subcommands for scitex-audio CLI."""

import sys

import click


@click.group(invoke_without_command=True)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
@click.pass_context
def mcp(ctx, as_json):
    """MCP (Model Context Protocol) server operations for audio."""
    if ctx.invoked_subcommand is None:
        if as_json:
            from . import group_to_json

            group_to_json(ctx, mcp)
        else:
            click.echo(ctx.get_help())


@mcp.command()
@click.option(
    "-t",
    "--transport",
    type=click.Choice(["stdio", "sse", "http"]),
    default="stdio",
    help="Transport protocol (default: stdio)",
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host for HTTP/SSE transport (default: 0.0.0.0)",
)
@click.option(
    "--port",
    default=31293,
    type=int,
    help="Port for HTTP/SSE transport (default: 31293)",
)
def start(transport, host, port):
    """Start the MCP server for remote audio playback.

    \b
    Examples:
      scitex-audio mcp start
      scitex-audio mcp start -t http --port 31293
    """
    try:
        from scitex_audio.mcp_server import FASTMCP_AVAILABLE, run_server

        if not FASTMCP_AVAILABLE:
            click.secho("Error: fastmcp not installed", fg="red", err=True)
            click.echo("\nInstall with:")
            click.echo("  pip install fastmcp")
            sys.exit(1)

        if transport != "stdio":
            click.secho(f"Starting scitex-audio MCP server ({transport})", fg="cyan")
            click.echo(f"  Host: {host}")
            click.echo(f"  Port: {port}")
            click.echo()
            click.echo("Remote agents can connect via SSH tunnel:")
            click.echo(f"  ssh -L {port}:localhost:{port} <this-host>")
            click.echo()

        run_server(transport=transport, host=host, port=port)

    except ImportError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        click.echo("\nInstall dependencies:")
        click.echo("  pip install fastmcp")
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


@mcp.command()
def doctor():
    """
    Check MCP server health and dependencies

    \b
    Example:
      scitex-audio mcp doctor
    """
    click.secho("Audio MCP Server Health Check", fg="cyan", bold=True)
    click.echo()

    click.echo("Checking FastMCP... ", nl=False)
    try:
        from scitex_audio.mcp_server import FASTMCP_AVAILABLE

        if FASTMCP_AVAILABLE:
            click.secho("OK", fg="green")
        else:
            click.secho("NOT INSTALLED", fg="red")
            click.echo("  Install with: pip install fastmcp")
    except ImportError:
        click.secho("FAIL", fg="red")

    click.echo("Checking audio backends... ", nl=False)
    try:
        from scitex_audio import available_backends

        backends = available_backends()
        if backends:
            click.secho(f"OK ({', '.join(backends)})", fg="green")
        else:
            click.secho("NONE AVAILABLE", fg="yellow")
    except Exception as e:
        click.secho(f"FAIL ({e})", fg="red")


@mcp.command("list-tools")
@click.option(
    "-v", "--verbose", count=True, help="Verbosity: -v sig, -vv +desc, -vvv full"
)
@click.option("-c", "--compact", is_flag=True, help="Compact signatures (single line)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_tools(ctx, verbose, compact, as_json):
    """List available audio MCP tools."""
    try:
        from scitex.cli.mcp import list_tools as main_list_tools

        ctx.invoke(
            main_list_tools,
            verbose=verbose,
            compact=compact,
            module="audio",
            as_json=as_json,
        )
    except ImportError:
        import json as json_mod

        tools = [
            {
                "name": "audio_speak",
                "description": "Convert text to speech with fallback",
            },
            {"name": "list_backends", "description": "List available TTS backends"},
            {
                "name": "check_audio_status",
                "description": "Check WSL audio connectivity",
            },
            {
                "name": "announce_context",
                "description": "Announce current directory and branch",
            },
        ]
        if as_json:
            click.echo(json_mod.dumps({"success": True, "tools": tools}, indent=2))
        else:
            click.secho("Audio MCP Tools", fg="cyan", bold=True)
            click.echo("=" * 40)
            for t in tools:
                name = click.style(t["name"], fg="green")
                click.echo(f"  {name}: {t['description']}")
                if verbose >= 1:
                    click.echo("    Use via: scitex-audio mcp start")
                    click.echo()


@mcp.command(
    "installation",
    hidden=True,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
def installation_deprecated(ctx):
    """(deprecated) Renamed to `show-installation`."""
    click.echo(
        "error: `scitex-audio mcp installation` was renamed to "
        "`scitex-audio mcp show-installation`.\n"
        "Re-run with: scitex-audio mcp show-installation",
        err=True,
    )
    ctx.exit(2)


@mcp.command("show-installation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_installation(as_json):
    """
    Show MCP server installation instructions for Claude Code

    \b
    Example:
      scitex-audio mcp show-installation
      scitex-audio mcp show-installation --json
    """
    import json as json_mod

    config = {
        "mcpServers": {
            "scitex-audio": {
                "command": "scitex-audio",
                "args": ["mcp", "start"],
            }
        }
    }
    if as_json:
        click.echo(json_mod.dumps({"success": True, "config": config}, indent=2))
    else:
        click.secho("MCP Server Installation", fg="cyan", bold=True)
        click.echo()
        click.echo("Add to your Claude Code settings (~/.claude/settings.json):")
        click.echo()
        click.echo(json_mod.dumps(config, indent=2))
        click.echo()
        click.echo("Or start manually:")
        click.echo("  scitex-audio mcp start")


# EOF
