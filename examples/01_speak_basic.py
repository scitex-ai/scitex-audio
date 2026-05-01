#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 01: Basic text-to-speech.

Demonstrates the simplest usage of scitex-audio:
- Auto-selects the best available backend
- Speaks text with default settings

Usage:
    python 01_speak_basic.py
"""

import scitex as stx

from scitex_audio import available_backends, speak


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Speak a greeting using the auto-selected TTS backend."""
    backends = available_backends()
    logger.info(f"Available backends: {backends}")

    if not backends:
        logger.info("No TTS backends installed. Install one:")
        logger.info("  pip install pyttsx3   # + apt install espeak-ng")
        logger.info("  pip install gTTS      # requires internet")
        return 0

    result = speak("Hello from SciTeX Audio!", play=True)
    logger.info(f"Backend used: {result.get('backend')}")
    logger.info(f"Audio played: {result.get('played')}")

    return 0


if __name__ == "__main__":
    main()
