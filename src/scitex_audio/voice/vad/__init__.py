#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/vad/__init__.py

"""Voice-activity detection for SciTeX Voice V1.

Finds speech-vs-silence spans; it does NOT decide *who* is speaking (that
is the verify gate). Two backends:
  * ``silero`` (default) — neural, robust to café noise; lazy torch.
  * ``energy`` — pure-numpy RMS gate; zero-dependency fallback + tests.
"""

from __future__ import annotations

from typing import List

import numpy as np

from ._energy import energy_vad
from ._segment import Segment, merge_segments

__all__ = ["Segment", "merge_segments", "energy_vad", "segment_speech"]


def segment_speech(
    wav: np.ndarray,
    sample_rate: int = 16000,
    backend: str = "silero",
    **kwargs,
) -> List[Segment]:
    """Segment a waveform into speech spans using the chosen backend.

    Args:
        wav: 1-D mono waveform, float32 @ ``sample_rate``.
        sample_rate: Samples per second (16 kHz for V1).
        backend: "silero" (default, neural) or "energy" (numpy fallback).
        **kwargs: Forwarded to the backend.

    Returns:
        List of ``Segment`` speech spans.
    """
    if backend == "energy":
        return energy_vad(wav, sample_rate, **kwargs)
    if backend == "silero":
        from ._silero import silero_vad  # lazy: keeps torch optional

        return silero_vad(wav, sample_rate, **kwargs)
    raise ValueError(f"unknown VAD backend {backend!r}; use 'silero' or 'energy'")
