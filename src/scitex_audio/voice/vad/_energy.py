#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/vad/_energy.py

"""Energy-gate VAD — the pure-numpy fallback backend (SciTeX Voice V1).

Frame RMS above an adaptive threshold = speech. This is deliberately the
*fallback*: Silero (see ``_silero``) is the default in a café because an
energy gate cannot tell the operator's speech from a neighbour's — that is
the verifier's job downstream, not the VAD's. But the energy gate needs no
model, so it keeps the pipeline testable and gives a zero-dependency path.

No admit/discard threshold here — this only finds *speech vs silence*, not
*who* is speaking.
"""

from __future__ import annotations

from typing import List

import numpy as np

from ..io._frame import frame_signal, ms_to_samples
from ._segment import Segment, merge_segments

__all__ = ["energy_vad"]


def energy_vad(
    wav: np.ndarray,
    sample_rate: int = 16000,
    frame_ms: float = 30.0,
    hop_ms: float = 10.0,
    threshold_db: float = -35.0,
    min_speech_ms: float = 150.0,
    merge_gap_ms: float = 200.0,
) -> List[Segment]:
    """Return speech segments via an RMS-energy gate.

    Args:
        wav: 1-D mono waveform, float32 in roughly [-1, 1].
        sample_rate: Samples per second.
        frame_ms: Analysis frame length.
        hop_ms: Hop between frames.
        threshold_db: Frames with RMS above this (dBFS) count as speech.
        min_speech_ms: Drop speech runs shorter than this.
        merge_gap_ms: Bridge silences up to this long.

    Returns:
        List of merged ``Segment`` spans, start-sorted.
    """
    wav = np.asarray(wav, dtype=np.float32).reshape(-1)
    frames, starts = frame_signal(wav, sample_rate, frame_ms, hop_ms)
    if frames.shape[0] == 0:
        return []

    rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-12)
    rms_db = 20.0 * np.log10(rms + 1e-12)
    voiced = rms_db > threshold_db

    frame_len = ms_to_samples(frame_ms, sample_rate)
    segments: List[Segment] = []
    run_start = None
    for i, is_voiced in enumerate(voiced):
        if is_voiced and run_start is None:
            run_start = int(starts[i])
        elif not is_voiced and run_start is not None:
            segments.append(Segment(run_start, int(starts[i - 1]) + frame_len, sample_rate))
            run_start = None
    if run_start is not None:
        segments.append(Segment(run_start, int(starts[-1]) + frame_len, sample_rate))

    merged = merge_segments(segments, merge_gap_ms)
    min_len = ms_to_samples(min_speech_ms, sample_rate)
    return [s for s in merged if (s.end - s.start) >= min_len]


# EOF
