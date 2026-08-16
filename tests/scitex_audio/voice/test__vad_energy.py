#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__vad_energy.py

"""Tests for the pure-numpy energy VAD + segment utilities (SciTeX Voice V1)."""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.vad import Segment, energy_vad, merge_segments, segment_speech


def _tone(n, sr=16000, freq=200.0, amp=0.5):
    """A mono sine tone of ``n`` samples — a stand-in for voiced speech."""
    t = np.arange(n, dtype=np.float32) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_segment_duration_in_seconds():
    # Arrange
    seg = Segment(0, 16000, 16000)

    # Act
    duration = seg.duration_s

    # Assert
    assert duration == pytest.approx(1.0)


def test_segment_end_in_seconds():
    # Arrange
    seg = Segment(0, 16000, 16000)

    # Act
    end = seg.end_s

    # Assert
    assert end == pytest.approx(1.0)


def test_empty_segment_is_rejected():
    # Arrange
    bounds = (100, 100)

    # Act
    # Assert
    with pytest.raises(ValueError):
        Segment(*bounds, 16000)


def test_merge_bridges_small_gap_into_one():
    # Arrange
    a = Segment(0, 1600, 16000)
    b = Segment(1600 + 800, 5000, 16000)  # 50 ms gap

    # Act
    merged = merge_segments([a, b], gap_ms=200)

    # Assert
    assert len(merged) == 1


def test_merge_bridged_segment_spans_full_range():
    # Arrange
    a = Segment(0, 1600, 16000)
    b = Segment(1600 + 800, 5000, 16000)

    # Act
    merged = merge_segments([a, b], gap_ms=200)

    # Assert
    assert (merged[0].start, merged[0].end) == (0, 5000)


def test_merge_keeps_segments_across_large_gap():
    # Arrange
    a = Segment(0, 1600, 16000)
    b = Segment(1600 + 16000, 20000, 16000)  # 1 s gap

    # Act
    merged = merge_segments([a, b], gap_ms=200)

    # Assert
    assert len(merged) == 2


def test_energy_vad_finds_single_speech_segment():
    # Arrange
    sr = 16000
    wav = np.concatenate([np.zeros(sr // 2, dtype=np.float32), _tone(sr, sr), np.zeros(sr // 2, dtype=np.float32)])

    # Act
    segs = energy_vad(wav, sr, threshold_db=-40.0, min_speech_ms=150.0)

    # Assert
    assert len(segs) == 1


def test_energy_vad_locates_speech_onset():
    # Arrange
    sr = 16000
    wav = np.concatenate([np.zeros(sr // 2, dtype=np.float32), _tone(sr, sr), np.zeros(sr // 2, dtype=np.float32)])

    # Act
    segs = energy_vad(wav, sr, threshold_db=-40.0, min_speech_ms=150.0)

    # Assert
    assert segs[0].start_s == pytest.approx(0.5, abs=0.05)


def test_energy_vad_pure_silence_returns_nothing():
    # Arrange
    wav = np.zeros(16000, dtype=np.float32)

    # Act
    segs = energy_vad(wav, 16000)

    # Assert
    assert segs == []


def test_segment_speech_dispatches_to_energy_backend():
    # Arrange
    wav = np.concatenate([np.zeros(8000, dtype=np.float32), _tone(16000)])

    # Act
    segs = segment_speech(wav, 16000, backend="energy", threshold_db=-40.0)

    # Assert
    assert len(segs) == 1


def test_segment_speech_rejects_unknown_backend():
    # Arrange
    wav = np.zeros(16000, dtype=np.float32)

    # Act
    # Assert
    with pytest.raises(ValueError, match="unknown VAD backend"):
        segment_speech(wav, 16000, backend="bogus")
