#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/asr/__init__.py

"""ASR adapter for SciTeX Voice V1.

Reuses the existing local whisper.cpp wrapper (``scitex_audio._stt``);
transcribes only the segments the verify gate admitted.
"""

from ._asr import transcribe_segment, transcribe_segments

__all__ = [
    "transcribe_segment",
    "transcribe_segments",
]
