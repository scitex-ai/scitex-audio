#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__frame.py

"""Tests for scitex_audio.voice.io._frame (SciTeX Voice V1)."""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.io import frame_signal, ms_to_samples


def test_ms_to_samples_for_30ms_frame():
    # Arrange
    ms = 30

    # Act
    n = ms_to_samples(ms, 16000)

    # Assert
    assert n == 480


def test_ms_to_samples_for_10ms_hop():
    # Arrange
    ms = 10

    # Act
    n = ms_to_samples(ms, 16000)

    # Assert
    assert n == 160


def test_frame_output_has_expected_shape():
    # Arrange
    wav = np.zeros(16000, dtype=np.float32)  # 1 s

    # Act
    frames, _starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10)

    # Assert
    assert frames.shape == (98, 480)  # (16000 - 480) // 160 + 1


def test_frame_starts_advance_by_hop():
    # Arrange
    wav = np.zeros(16000, dtype=np.float32)

    # Act
    _frames, starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10)

    # Assert
    assert starts[1] - starts[0] == 160


def test_short_input_without_pad_yields_no_frames():
    # Arrange
    wav = np.zeros(100, dtype=np.float32)

    # Act
    frames, _starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10, pad=False)

    # Assert
    assert frames.shape == (0, 480)


def test_short_input_with_pad_yields_single_frame():
    # Arrange
    wav = np.ones(100, dtype=np.float32)

    # Act
    frames, _starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10, pad=True)

    # Assert
    assert frames.shape[0] == 1


def test_short_input_with_pad_zeroes_the_tail():
    # Arrange
    wav = np.ones(100, dtype=np.float32)

    # Act
    frames, _starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10, pad=True)

    # Assert
    assert frames[0, 100:].sum() == pytest.approx(0.0)


def test_frames_are_writable_copies_not_views():
    # Arrange
    wav = np.arange(2000, dtype=np.float32)

    # Act
    frames, _starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10)
    frames[0, 0] = -999.0

    # Assert
    assert wav[0] == 0.0


def test_non_positive_frame_length_raises():
    # Arrange
    wav = np.zeros(100)

    # Act
    # Assert
    with pytest.raises(ValueError):
        frame_signal(wav, 16000, frame_ms=0, hop_ms=10)
