#!/usr/bin/env python3
"""``list-backends`` and ``check-backends`` commands for the scitex-audio CLI."""

import sys

import click


def register(group):
    @group.command(name="list-backends")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def list_backends(as_json):
        """
        List available TTS backends

        \b
        Example:
          scitex-audio backends
          scitex-audio backends --json
        """
        try:
            from scitex_audio import FALLBACK_ORDER, available_backends

            backends = available_backends()

            if as_json:
                from scitex_dev import Result

                data = {
                    "available": backends,
                    "fallback_order": FALLBACK_ORDER,
                }
                click.echo(Result(success=True, data=data).to_json())
            else:
                click.secho("Available TTS Backends", fg="cyan", bold=True)
                click.echo("=" * 40)

                click.echo("\nFallback order:")
                for i, b in enumerate(FALLBACK_ORDER, 1):
                    status = (
                        click.style("available", fg="green")
                        if b in backends
                        else click.style("not installed", fg="red")
                    )
                    click.echo(f"  {i}. {b}: {status}")

                if not backends:
                    click.echo()
                    click.secho("No backends available!", fg="red")
                    click.echo("Install one of:")
                    click.echo("  pip install pyttsx3  # + apt install espeak-ng")
                    click.echo("  pip install gTTS")
                    click.echo("  pip install elevenlabs")

        except Exception as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)

    @group.command("check-backends")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def check_backends(as_json):
        """
        Check audio status (especially for WSL)

        \b
        Checks:
          - WSL detection
          - WSLg availability
          - PulseAudio connection
          - Windows fallback availability

        \b
        Example:
          scitex-audio check
          scitex-audio check --json
        """
        try:
            from scitex_audio import check_wsl_audio

            status = check_wsl_audio()

            if as_json:
                from scitex_dev import Result

                click.echo(Result(success=True, data=status).to_json())
            else:
                click.secho("Audio Status Check", fg="cyan", bold=True)
                click.echo("=" * 40)

                def status_mark(val):
                    return (
                        click.style("Yes", fg="green")
                        if val
                        else click.style("No", fg="red")
                    )

                click.echo(f"\nWSL Environment: {status_mark(status['is_wsl'])}")

                if status["is_wsl"]:
                    click.echo(
                        f"WSLg Available: {status_mark(status['wslg_available'])}"
                    )
                    click.echo(
                        f"PulseServer Socket: "
                        f"{status_mark(status['pulse_server_exists'])}"
                    )
                    click.echo(
                        f"PulseAudio Connected: "
                        f"{status_mark(status['pulse_connected'])}"
                    )
                    click.echo(
                        f"Windows Fallback: "
                        f"{status_mark(status['windows_fallback_available'])}"
                    )

                click.echo()
                rec = status["recommended"]
                if rec == "linux":
                    click.secho("Recommended: Linux audio (PulseAudio)", fg="green")
                elif rec == "windows":
                    click.secho(
                        "Recommended: Windows fallback (powershell.exe)", fg="yellow"
                    )
                else:
                    click.secho("No audio output available", fg="red")

        except Exception as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)

    return list_backends, check_backends


# EOF
