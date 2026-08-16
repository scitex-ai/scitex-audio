#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/asr/_asr.py

"""ASR adapter for SciTeX Voice V1.

Thin layer over the package's existing local whisper.cpp wrapper
(``scitex_audio._stt``) — no new ASR engine. Its job is segment-level
transcription: given the waveform and the segments the verify gate
*admitted*, transcribe only those and stitch the text. Everything the
verifier discarded (neighbours, BGM) never reaches Whisper — the privacy +
café-noise property the whole pipeline exists for.

whisper.cpp runs locally with no API (non-negotiable #1). On compute-03's
GTX 1070 build whisper.cpp against CUDA 12.x (CUDA 13 dropped offline
Pascal support); the M0 microbench picks the largest interactive model.
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional, Sequence

import numpy as np

from ... import _stt
from ..io._wav import TARGET_SR, write_wav
from ..vad._segment import Segment

__all__ = ["transcribe_segment", "transcribe_segments"]


def transcribe_segment(
    wav: np.ndarray,
    segment: Segment,
    language: Optional[str] = "ja",
    model: str = "tiny",
) -> dict:
    """Transcribe a single admitted segment's audio.

    Slices ``wav`` to ``segment``, writes a temp 16 kHz WAV, and delegates
    to ``scitex_audio._stt.transcribe`` (whisper.cpp).

    Args:
        wav: Full 1-D mono waveform the segment indexes into.
        segment: The admitted speech span.
        language: Whisper language code, or None to auto-detect.
        model: Whisper model name.

    Returns:
        The ``_stt.transcribe`` result dict, plus ``start_s``/``end_s`` of
        the segment for downstream ordering.
    """
    wav = np.asarray(wav, dtype=np.float32).reshape(-1)
    clip = wav[segment.start : segment.end]
    fd, tmp_wav = tempfile.mkstemp(suffix=".wav", prefix="scitex_voice_asr_")
    os.close(fd)
    try:
        write_wav(tmp_wav, clip, segment.sample_rate or TARGET_SR)
        result = _stt.transcribe(tmp_wav, language=language, model=model)
    finally:
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass
    result["start_s"] = segment.start_s
    result["end_s"] = segment.end_s
    return result


def transcribe_segments(
    wav: np.ndarray,
    segments: Sequence[Segment],
    language: Optional[str] = "ja",
    model: str = "tiny",
) -> List[dict]:
    """Transcribe each admitted segment, in time order.

    Args:
        wav: Full 1-D mono waveform.
        segments: Admitted speech spans (from the verify gate).
        language: Whisper language code, or None to auto-detect.
        model: Whisper model name.

    Returns:
        Per-segment result dicts, sorted by segment start.
    """
    ordered = sorted(segments, key=lambda s: s.start)
    return [transcribe_segment(wav, s, language, model) for s in ordered]


# EOF
