#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/io/__init__.py

"""Audio I/O and framing for SciTeX Voice V1.

Canonical form for the pipeline is mono float32 @ 16 kHz. ``frame_signal``
is pure-numpy; wav read/write import soundfile lazily.
"""

from ._frame import frame_signal, ms_to_samples
from ._wav import TARGET_SR, read_wav, to_mono, write_wav

__all__ = [
    "TARGET_SR",
    "frame_signal",
    "ms_to_samples",
    "read_wav",
    "to_mono",
    "write_wav",
]
