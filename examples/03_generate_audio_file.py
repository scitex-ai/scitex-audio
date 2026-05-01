#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 03: Generate audio files without playback.

Demonstrates:
- Generating audio bytes
- Saving to file without playing
- Using generate_bytes() for programmatic access

Usage:
    python 03_generate_audio_file.py
"""

from pathlib import Path

import scitex as stx

from scitex_audio import available_backends, generate_bytes, speak


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Render speech to disk without playback."""
    OUT = Path(CONFIG.SDIR_OUT)

    backends = available_backends()
    if not backends:
        logger.info("No TTS backends available.")
        return 0

    # Save to file without playing
    output_path = OUT / "greeting.mp3"
    result = speak(
        "This audio was saved to a file.",
        output_path=str(output_path),
        play=False,
    )
    logger.info(f"Saved audio to: {output_path}")
    logger.info(f"speak() result: backend={result.get('backend')}")

    # Generate raw bytes (useful for streaming/HTTP responses)
    audio_bytes = generate_bytes("Hello as bytes")
    logger.info(f"Generated {len(audio_bytes)} bytes of audio")

    # Save bytes manually
    bytes_path = OUT / "bytes_output.mp3"
    bytes_path.write_bytes(audio_bytes)
    logger.info(f"Saved bytes to: {bytes_path}")

    return 0


if __name__ == "__main__":
    main()
