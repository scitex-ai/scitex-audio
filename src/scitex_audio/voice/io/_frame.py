#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/io/_frame.py

"""Frame a mono waveform into fixed windows for VAD / embedding.

Pure-numpy, no heavy deps. This is the tiling primitive shared by the VAD
(short frames) and enrolment (longer overlapping windows -> one embedding
each). Part of SciTeX Voice V1; see card
scitex-voice-speaker-verified-dictation-v1-20260816.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

__all__ = ["frame_signal", "ms_to_samples"]


def ms_to_samples(ms: float, sample_rate: int) -> int:
    """Convert a duration in milliseconds to a whole number of samples."""
    return int(round(ms * sample_rate / 1000.0))


def frame_signal(
    wav: np.ndarray,
    sample_rate: int = 16000,
    frame_ms: float = 30.0,
    hop_ms: float = 10.0,
    pad: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """Slice a 1-D waveform into overlapping frames.

    Args:
        wav: 1-D mono waveform.
        sample_rate: Samples per second (16 kHz for the V1 pipeline).
        frame_ms: Frame length in milliseconds.
        hop_ms: Hop (stride) between frame starts in milliseconds.
        pad: If True, zero-pad the tail so every sample appears in at least
            one frame; if False, drop a trailing remainder shorter than one
            frame.

    Returns:
        ``(frames, starts)`` where ``frames`` has shape
        ``(n_frames, frame_len)`` and ``starts`` holds each frame's start
        sample index. ``n_frames == 0`` for input shorter than one frame
        (with ``pad=False``).
    """
    wav = np.asarray(wav, dtype=np.float32).reshape(-1)
    frame_len = ms_to_samples(frame_ms, sample_rate)
    hop_len = ms_to_samples(hop_ms, sample_rate)
    if frame_len <= 0 or hop_len <= 0:
        raise ValueError("frame_ms and hop_ms must be > 0")

    n = wav.shape[0]
    if n < frame_len:
        if not pad:
            return np.empty((0, frame_len), dtype=np.float32), np.empty(
                (0,), dtype=np.int64
            )
        wav = np.pad(wav, (0, frame_len - n))
        n = frame_len

    if pad:
        remainder = (n - frame_len) % hop_len
        if remainder:
            wav = np.pad(wav, (0, hop_len - remainder))
            n = wav.shape[0]

    n_frames = 1 + (n - frame_len) // hop_len
    starts = np.arange(n_frames, dtype=np.int64) * hop_len
    # Strided view -> contiguous copy so downstream writes are safe.
    idx = starts[:, None] + np.arange(frame_len)[None, :]
    frames = wav[idx].astype(np.float32, copy=True)
    return frames, starts


# EOF
