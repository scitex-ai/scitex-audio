#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/vad/_segment.py

"""Speech-segment value type and span utilities (SciTeX Voice V1).

A ``Segment`` is a half-open ``[start, end)`` span in samples. The verify
gate scores each segment's embedding; the pipeline sends only admitted
segments to ASR. Pure-python, no heavy deps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

__all__ = ["Segment", "merge_segments"]


@dataclass(frozen=True)
class Segment:
    """A half-open speech span ``[start, end)`` measured in samples."""

    start: int
    end: int
    sample_rate: int = 16000

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(f"empty/negative segment: [{self.start}, {self.end})")

    @property
    def duration_s(self) -> float:
        return (self.end - self.start) / self.sample_rate

    @property
    def start_s(self) -> float:
        return self.start / self.sample_rate

    @property
    def end_s(self) -> float:
        return self.end / self.sample_rate


def merge_segments(
    segments: List[Segment], gap_ms: float = 200.0
) -> List[Segment]:
    """Merge segments separated by <= ``gap_ms`` of silence.

    Bridges the brief pauses within a phrase so the verifier scores whole
    utterances rather than syllable fragments. Assumes a single sample rate.

    Args:
        segments: Segments, not necessarily sorted.
        gap_ms: Max inter-segment silence to bridge, in milliseconds.

    Returns:
        A new, start-sorted list of merged segments.
    """
    if not segments:
        return []
    sr = segments[0].sample_rate
    gap = int(round(gap_ms * sr / 1000.0))
    ordered = sorted(segments, key=lambda s: s.start)
    merged = [ordered[0]]
    for seg in ordered[1:]:
        last = merged[-1]
        if seg.start - last.end <= gap:
            merged[-1] = Segment(last.start, max(last.end, seg.end), sr)
        else:
            merged.append(seg)
    return merged


# EOF
