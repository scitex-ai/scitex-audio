#!/usr/bin/env python3
# Timestamp: "2025-12-11 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-code/src/scitex/audio/engines/__init__.py
# ----------------------------------------

"""
TTS Engine Backends

Fallback order: elevenlabs -> luxtts -> gtts -> pyttsx3

Engines:
    - SystemTTS (pyttsx3): Offline, free, uses system TTS
    - GoogleTTS (gtts): Free, requires internet
    - ElevenLabsTTS: Paid, high quality
"""

# Import engines (fail gracefully if dependencies missing)
# Note: BaseTTS and TTSBackend are internal - import from ._base if needed
from scitex_dev import try_import_optional

SystemTTS = try_import_optional(
    "._pyttsx3_engine",
    attr="SystemTTS",
    extra="pyttsx3",
    pkg="scitex-audio",
    package=__name__,
)
GoogleTTS = try_import_optional(
    "._gtts_engine",
    attr="GoogleTTS",
    extra="gtts",
    pkg="scitex-audio",
    package=__name__,
)
ElevenLabsTTS = try_import_optional(
    "._elevenlabs_engine",
    attr="ElevenLabsTTS",
    extra="elevenlabs",
    pkg="scitex-audio",
    package=__name__,
)
LuxTTS = try_import_optional(
    "._luxtts_engine",
    attr="LuxTTS",
    extra="luxtts",
    pkg="scitex-audio",
    package=__name__,
)

__all__ = [
    "SystemTTS",
    "GoogleTTS",
    "ElevenLabsTTS",
    "LuxTTS",
]

# EOF
