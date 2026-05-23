#!/usr/bin/env python3
"""``speak-text`` command for the scitex-audio CLI."""

import sys

import click


def build_speak_kwargs(text, backend, voice, output, no_play, rate, speed, no_fallback):
    """Translate ``speak-text`` CLI options into ``speak()`` kwargs.

    Pure function — no I/O, no globals. The CLI layer is a thin translator
    from option flags to the ``scitex_audio.speak`` API, so this is the unit
    worth testing directly.
    """
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
    return kwargs


def register(group):
    @group.command("speak-text")
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
    @click.option(
        "--rate", "-r", type=int, help="Speech rate (pyttsx3 only, default: 150)"
    )
    @click.option(
        "--speed", "-s", type=float, help="Speed multiplier (gtts only, e.g., 1.5)"
    )
    @click.option(
        "--no-fallback", is_flag=True, help="Disable backend fallback on error"
    )
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

        kwargs = build_speak_kwargs(
            text, backend, voice, output, no_play, rate, speed, no_fallback
        )

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

    return speak_text


# EOF
