#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 02: Backend selection and voice configuration.

Demonstrates:
- Listing available backends
- Selecting a specific backend
- Configuring voice/language
- Speed control

Usage:
    python 02_backends_and_voices.py
"""

import scitex as stx

from scitex_audio import FALLBACK_ORDER, available_backends, get_tts


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Show fallback order and exercise per-backend voice selection."""
    backends = available_backends()

    logger.info("TTS Backend Fallback Order:")
    for b in FALLBACK_ORDER:
        status = "available" if b in backends else "not installed"
        logger.info(f"  {b}: {status}")

    # Use a specific backend if available
    if "gtts" in backends:
        tts = get_tts("gtts")
        voices = tts.get_voices()
        logger.info(f"Google TTS languages: {len(voices)} available")
        for v in voices[:5]:
            logger.info(f"  {v['name']} ({v['id']})")

        result = tts.speak("Bonjour le monde", voice="fr", play=True)
        logger.info(f"Spoke in French: played={result.get('played')}")
    else:
        logger.info("gtts backend not installed; skipping voice demo.")

    return 0


if __name__ == "__main__":
    main()
