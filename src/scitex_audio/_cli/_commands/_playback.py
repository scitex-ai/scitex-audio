#!/usr/bin/env python3
"""``stop-playback`` and ``relay`` commands for the scitex-audio CLI."""

import sys

import click


def register(group):
    @group.command("stop-playback")
    @click.option(
        "--json",
        "as_json",
        is_flag=True,
        help="Output as structured JSON (Result envelope).",
    )
    @click.option(
        "--dry-run", is_flag=True, help="Print plan without stopping playback."
    )
    @click.option(
        "-y",
        "--yes",
        is_flag=True,
        help="Suppress interactive confirmation (assume yes).",
    )
    def stop_playback(as_json, dry_run, yes):
        """
        Stop any currently playing speech

        \b
        Example:
          scitex-audio stop-playback
          scitex-audio stop-playback --json
          scitex-audio stop-playback --dry-run
        """
        if dry_run:
            click.echo("DRY RUN — would stop any active speech playback")
            return
        if as_json:
            from scitex_dev import wrap_as_cli

            from scitex_audio import stop_speech

            wrap_as_cli(stop_speech, as_json=True)
            return
        try:
            from scitex_audio import stop_speech

            stop_speech()
            click.secho("Speech stopped", fg="green")
        except Exception as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)

    @group.command()
    @click.option(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    @click.option(
        "--port",
        default=31293,
        type=int,
        help="Port to bind (default: 31293)",
    )
    @click.option(
        "--force",
        is_flag=True,
        help="Kill existing process using the port if any",
    )
    def relay(host, port, force):
        """
        Run simple HTTP relay server for remote audio playback

        \b
        Endpoints: POST /speak, GET /health, GET /list_backends

        \b
        Example:
          scitex-audio relay --port 31293
          # Remote: export SCITEX_AUDIO_RELAY_URL=http://LOCAL_IP:31293
          # Or SSH: ssh -R 31293:localhost:31293 remote-server
        """
        try:
            from scitex_audio.mcp_server import run_relay_server

            if force:
                from scitex_audio._utils import kill_process_on_port

                kill_process_on_port(port)

            click.secho("Starting audio relay server", fg="cyan")
            click.echo(f"  Host: {host}")
            click.echo(f"  Port: {port}")
            click.echo()
            click.echo("Endpoints:")
            click.echo("  POST /speak       - Play text-to-speech")
            click.echo("  GET  /health      - Health check")
            click.echo("  GET  /list_backends - List backends")
            click.echo()

            run_relay_server(host=host, port=port, force=force)

        except Exception as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)

    return stop_playback, relay


# EOF
