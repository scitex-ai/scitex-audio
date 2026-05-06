#!/usr/bin/env python3
"""
SciTeX CLI - Audio Commands (Text-to-Speech)

Provides text-to-speech with multiple backend support.
"""

import sys

import click

from scitex_audio import __version__


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(
    __version__, "-V", "--version", message="scitex-audio %(version)s"
)
@click.option("--help-recursive", is_flag=True, help="Show help for all subcommands")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
@click.pass_context
def audio(ctx, help_recursive, as_json):
    """
    Text-to-speech utilities

    \b
    Config is loaded with the SciTeX precedence chain:
      config.yaml -> $SCITEX_AUDIO_CONFIG -> ~/.scitex/audio/config.yaml -> defaults

    \b
    Backends (fallback order):
      elevenlabs - ElevenLabs (paid, high quality)
      luxtts     - LuxTTS (open-source, offline, voice-cloning)
      gtts       - Google TTS (free, needs internet)
      pyttsx3    - System TTS (offline, free)

    \b
    Examples:
      scitex-audio speak-text "Hello world"
      scitex-audio speak-text "Bonjour" --backend gtts --voice fr
      scitex-audio list-backends         # List available backends
      scitex-audio check-backends        # Check audio status (WSL)
    """
    if help_recursive:
        from . import print_help_recursive

        print_help_recursive(ctx, audio)
        ctx.exit(0)
    elif ctx.invoked_subcommand is None:
        if as_json:
            from . import group_to_json

            group_to_json(ctx, audio)
        else:
            click.echo(ctx.get_help())


def _deprecated_redirect(old: str, new: str):
    """Build a hidden Click command that exits 2 with a re-run hint."""

    @click.pass_context
    def _impl(ctx, **_):
        click.echo(
            f"error: `scitex-audio {old}` was renamed to `scitex-audio {new}`.\n"
            f"Re-run with: scitex-audio {new} <args>",
            err=True,
        )
        ctx.exit(2)

    return click.command(
        old,
        hidden=True,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )(_impl)


audio.add_command(_deprecated_redirect("speak", "speak-text"))
audio.add_command(_deprecated_redirect("backends", "list-backends"))
audio.add_command(_deprecated_redirect("check", "check-backends"))
audio.add_command(_deprecated_redirect("stop", "stop-playback"))
audio.add_command(_deprecated_redirect("transcribe", "transcribe-audio"))
audio.add_command(_deprecated_redirect("env-template", "show-env-template"))


@audio.command("speak-text")
@click.argument("text")
@click.option(
    "--backend",
    "-b",
    type=click.Choice(["pyttsx3", "gtts", "luxtts", "elevenlabs"]),
    help="TTS backend (auto-selects with fallback if not specified)",
)
@click.option("--voice", "-v", help="Voice name, ID, or language code")
@click.option("--output", "-o", type=click.Path(), help="Save audio to file")
@click.option("--no-play", is_flag=True, help="Don't play audio (only save)")
@click.option("--rate", "-r", type=int, help="Speech rate (pyttsx3 only, default: 150)")
@click.option(
    "--speed", "-s", type=float, help="Speed multiplier (gtts only, e.g., 1.5)"
)
@click.option("--no-fallback", is_flag=True, help="Disable backend fallback on error")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
def speak_text(
    text, backend, voice, output, no_play, rate, speed, no_fallback, as_json
):
    """
    Convert text to speech

    \b
    Examples:
      scitex-audio speak "Hello world"
      scitex-audio speak "Bonjour" --backend gtts --voice fr
      scitex-audio speak "Test" --output speech.mp3 --no-play
      scitex-audio speak "Fast speech" --backend pyttsx3 --rate 200
      scitex-audio speak "Slow speech" --backend gtts --speed 0.8
      scitex-audio speak "Hello" --json
    """
    import logging
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    kwargs = {
        "text": text,
        "play": not no_play,
        "fallback": not no_fallback,
    }
    if backend:
        kwargs["backend"] = backend
    if voice:
        kwargs["voice"] = voice
    if output:
        kwargs["output_path"] = output
    if rate:
        kwargs["rate"] = rate
    if speed:
        kwargs["speed"] = speed

    if as_json:
        from scitex_dev import wrap_as_cli

        from scitex_audio import speak as tts_speak

        wrap_as_cli(tts_speak, as_json=True, **kwargs)
        return

    try:
        from scitex_audio import speak as tts_speak

        result = tts_speak(**kwargs)

        if output and result.get("path"):
            click.secho(f"Audio saved: {result['path']}", fg="green")

        if not no_play:
            if result.get("played"):
                click.secho("Speech completed (audio played)", fg="green")
            else:
                click.secho(
                    "Warning: Audio generated but playback failed (no speaker?)",
                    fg="yellow",
                )

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


@audio.command(name="list-backends")
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


@audio.command("check-backends")
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
                click.echo(f"WSLg Available: {status_mark(status['wslg_available'])}")
                click.echo(
                    f"PulseServer Socket: {status_mark(status['pulse_server_exists'])}"
                )
                click.echo(
                    f"PulseAudio Connected: {status_mark(status['pulse_connected'])}"
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


@audio.command("stop-playback")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
@click.option("--dry-run", is_flag=True, help="Print plan without stopping playback.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
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


# Register MCP subgroup from separate module
from ._mcp_cli import mcp

audio.add_command(mcp)

try:
    from scitex_dev.cli import docs_click_group

    audio.add_command(docs_click_group(package="scitex-audio"))
except ImportError:
    pass

try:
    from scitex_dev.cli import skills_click_group

    audio.add_command(skills_click_group(package="scitex-audio"))
except ImportError:
    pass


@audio.command()
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


@audio.command("transcribe-audio")
@click.argument("audio_path", type=click.Path(exists=True))
@click.option("--language", "-l", default="ja", help="Language code (default: ja)")
@click.option("--model", "-m", default="tiny", help="Whisper model (default: tiny)")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
def transcribe(audio_path, language, model, as_json):
    """
    Transcribe audio file to text using whisper.cpp

    \b
    Examples:
      scitex-audio transcribe recording.wav
      scitex-audio transcribe recording.wav -l en -m base
      scitex-audio transcribe recording.wav --json
    """
    try:
        from scitex_audio import transcribe as stt_transcribe

        result = stt_transcribe(
            audio_path=audio_path,
            language=language,
            model=model,
        )

        if as_json:
            import json as json_mod

            click.echo(json_mod.dumps(result, ensure_ascii=False, indent=2))
        elif result.get("success"):
            click.echo(result["text"])
        else:
            click.secho(
                f"Error: {result.get('error', 'Unknown error')}", fg="red", err=True
            )
            sys.exit(1)

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


@audio.command("show-env-template")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Write template to file instead of stdout",
)
@click.option(
    "--no-sensitive",
    is_flag=True,
    help="Exclude sensitive variables (API keys)",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as structured JSON (Result envelope).",
)
def env_template(output, no_sensitive, as_json):
    """
    Generate a template .src file for SCITEX_AUDIO_ENV_SRC

    \b
    Examples:
      scitex-audio show-env-template                    # Print to stdout
      scitex-audio show-env-template -o audio.src       # Write to file
      scitex-audio show-env-template --no-sensitive     # Exclude API keys
      scitex-audio show-env-template --json             # JSON envelope
    """
    from scitex_audio._env_registry import generate_template

    content = generate_template(include_sensitive=not no_sensitive)

    if as_json:
        from scitex_dev import Result

        click.echo(
            Result(
                success=True,
                data={"template": content, "include_sensitive": not no_sensitive},
            ).to_json()
        )
        return

    if output:
        from pathlib import Path

        Path(output).write_text(content + "\n")
        click.secho(f"Template written to {output}", fg="green")
        click.echo(f"  Usage: export SCITEX_AUDIO_ENV_SRC={output}")
    else:
        click.echo(content)


@audio.command("list-python-apis")
@click.option("-v", "--verbose", count=True, help="Verbosity: -v +doc, -vv full doc")
@click.option("-d", "--max-depth", type=int, default=5, help="Max recursion depth")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_python_apis(ctx, verbose, max_depth, as_json):
    """List Python APIs for scitex-audio.

    \b
    Example:
      $ scitex-audio list-python-apis
      $ scitex-audio list-python-apis -vv
      $ scitex-audio list-python-apis --json
    """
    try:
        from scitex.cli.introspect import api

        ctx.invoke(
            api,
            dotted_path="scitex_audio",
            verbose=verbose,
            max_depth=max_depth,
            as_json=as_json,
        )
    except ImportError:
        import inspect
        import json as json_mod

        import scitex_audio

        apis = []
        for name in scitex_audio.__all__:
            obj = getattr(scitex_audio, name, None)
            if obj is None:
                continue
            entry = {"name": name, "type": type(obj).__name__}
            if verbose >= 1 and callable(obj):
                try:
                    entry["signature"] = str(inspect.signature(obj))
                except (ValueError, TypeError):
                    pass
            if verbose >= 2 and obj.__doc__:
                entry["doc"] = obj.__doc__.strip().split("\n")[0]
            apis.append(entry)

        if as_json:
            click.echo(
                json_mod.dumps(
                    {"success": True, "module": "scitex_audio", "apis": apis},
                    indent=2,
                )
            )
        else:
            click.secho("scitex_audio Python APIs", fg="cyan", bold=True)
            click.echo("=" * 40)
            for a in apis:
                name = click.style(a["name"], fg="green")
                sig = a.get("signature", "")
                click.echo(f"  {name}{sig}")
                if "doc" in a:
                    click.echo(f"    {a['doc']}")


# §1a: install-shell-completion + print-shell-completion (canonical leaves)
try:
    from scitex_dev._cli._completion import attach_shell_completion

    attach_shell_completion(audio, prog_name="scitex-audio")
except ImportError:
    pass


if __name__ == "__main__":
    audio()

# EOF
