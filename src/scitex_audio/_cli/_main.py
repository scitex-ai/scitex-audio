#!/usr/bin/env python3
"""
SciTeX CLI - Audio Commands (Text-to-Speech)

Thin orchestrator: defines the ``audio`` Click group and registers each
subcommand from the focused modules under ``_cli/_commands/``.
"""

import click

from scitex_audio import __version__

from ._commands import (
    register_backends,
    register_env,
    register_playback,
    register_speak,
    register_stt,
    register_system_deps,
)


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

# Register subcommands from focused modules.
register_speak(audio)
register_backends(audio)
register_playback(audio)
register_stt(audio)
register_env(audio)
register_system_deps(audio)

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

# §1a: install-shell-completion + print-shell-completion (canonical leaves)
try:
    from scitex_dev._cli._completion import attach_shell_completion

    attach_shell_completion(audio, prog_name="scitex-audio")
except ImportError:
    pass


if __name__ == "__main__":
    audio()

# EOF
