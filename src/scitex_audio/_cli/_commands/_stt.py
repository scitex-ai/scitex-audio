#!/usr/bin/env python3
"""``transcribe-audio`` command for the scitex-audio CLI."""

import sys

import click


def register(group):
    @group.command("transcribe-audio")
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
                    f"Error: {result.get('error', 'Unknown error')}",
                    fg="red",
                    err=True,
                )
                sys.exit(1)

        except Exception as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)

    return transcribe


# EOF
