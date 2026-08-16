#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/vad/test__segment.py

"""Tests for scitex_audio.voice.vad._segment (SciTeX Voice V1)."""

from __future__ import annotations

import pytest

from scitex_audio.voice.vad import Segment, merge_segments


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
