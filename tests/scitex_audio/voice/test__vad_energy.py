#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__vad_energy.py

"""Tests for the pure-numpy energy VAD + segment utilities (SciTeX Voice V1)."""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.vad import Segment, energy_vad, merge_segments, segment_speech


def _tone(n, sr=16000, freq=200.0, amp=0.5):
    t = np.arange(n, dtype=np.float32) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_segment_duration_and_seconds():
    seg = Segment(0, 16000, 16000)
    assert seg.duration_s == pytest.approx(1.0)
    assert seg.end_s == pytest.approx(1.0)


def test_empty_segment_rejected():
    with pytest.raises(ValueError):
        Segment(100, 100, 16000)


def test_merge_bridges_small_gap():
    a = Segment(0, 1600, 16000)
    b = Segment(1600 + 800, 5000, 16000)  # 50 ms gap
    merged = merge_segments([a, b], gap_ms=200)
    assert len(merged) == 1
    assert merged[0].start == 0 and merged[0].end == 5000


def test_merge_keeps_large_gap():
    a = Segment(0, 1600, 16000)
    b = Segment(1600 + 16000, 20000, 16000)  # 1 s gap
    assert len(merge_segments([a, b], gap_ms=200)) == 2


def test_energy_vad_finds_speech_in_silence():
    sr = 16000
    silence = np.zeros(sr // 2, dtype=np.float32)
    speech = _tone(sr, sr)  # 1 s tone
    wav = np.concatenate([silence, speech, silence])
    segs = energy_vad(wav, sr, threshold_db=-40.0, min_speech_ms=150.0)
    assert len(segs) == 1
    # Speech starts around 0.5 s and lasts ~1 s.
    assert segs[0].start_s == pytest.approx(0.5, abs=0.05)
    assert segs[0].duration_s == pytest.approx(1.0, abs=0.1)


def test_energy_vad_pure_silence_returns_nothing():
    assert energy_vad(np.zeros(16000, dtype=np.float32), 16000) == []


def test_segment_speech_dispatch_energy():
    wav = np.concatenate([np.zeros(8000, dtype=np.float32), _tone(16000)])
    segs = segment_speech(wav, 16000, backend="energy", threshold_db=-40.0)
    assert len(segs) == 1


def test_segment_speech_unknown_backend():
    with pytest.raises(ValueError, match="unknown VAD backend"):
        segment_speech(np.zeros(16000, dtype=np.float32), 16000, backend="bogus")
