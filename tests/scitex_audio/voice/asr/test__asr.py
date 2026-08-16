#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/asr/test__asr.py

"""Tests for scitex_audio.voice.asr._asr (SciTeX Voice V1).

These exercise the adapter's segment handling (slice -> temp wav -> _stt)
without asserting a transcript: whisper.cpp is absent on CI, so
``scitex_audio._stt.transcribe`` returns a ``success=False`` dict, and the
adapter still stamps each result with its segment's time bounds and returns
them in time order. Writing the temp wav needs libsndfile (importorskip).
"""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.asr import transcribe_segments
from scitex_audio.voice.vad import Segment


@pytest.fixture
def two_out_of_order_segments():
    """A 1 s waveform + two segments given later-then-earlier."""
    pytest.importorskip("soundfile")
    wav = np.zeros(16000, dtype=np.float32)
    later = Segment(8000, 12000, 16000)
    earlier = Segment(1000, 4000, 16000)
    return wav, [later, earlier]


def test_transcribe_segments_returns_one_result_per_segment(two_out_of_order_segments):
    # Arrange
    wav, segments = two_out_of_order_segments

    # Act
    results = transcribe_segments(wav, segments, language=None, model="tiny")

    # Assert
    assert len(results) == 2


def test_transcribe_segments_orders_results_by_start_time(two_out_of_order_segments):
    # Arrange
    wav, segments = two_out_of_order_segments

    # Act
    results = transcribe_segments(wav, segments, language=None, model="tiny")

    # Assert
    assert results[0]["start_s"] < results[1]["start_s"]


def test_transcribe_segments_stamps_segment_time_bounds(two_out_of_order_segments):
    # Arrange
    wav, segments = two_out_of_order_segments

    # Act
    results = transcribe_segments(wav, segments, language=None, model="tiny")

    # Assert
    assert results[0]["start_s"] == pytest.approx(1000 / 16000)
