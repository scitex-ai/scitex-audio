#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__frame.py

"""Tests for scitex_audio.voice.io._frame (SciTeX Voice V1)."""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.io import frame_signal, ms_to_samples


def test_ms_to_samples():
    assert ms_to_samples(30, 16000) == 480
    assert ms_to_samples(10, 16000) == 160


def test_frame_count_and_shape():
    wav = np.zeros(16000, dtype=np.float32)  # 1 s
    frames, starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10)
    # (16000 - 480) // 160 + 1
    assert frames.shape == (98, 480)
    assert starts[0] == 0 and starts[1] == 160


def test_short_input_no_pad_returns_empty():
    wav = np.zeros(100, dtype=np.float32)
    frames, starts = frame_signal(wav, 16000, frame_ms=30, hop_ms=10, pad=False)
    assert frames.shape == (0, 480)
    assert starts.shape == (0,)


def test_short_input_pad_returns_one_frame():
    wav = np.ones(100, dtype=np.float32)
    frames, _ = frame_signal(wav, 16000, frame_ms=30, hop_ms=10, pad=True)
    assert frames.shape[0] == 1
    assert frames[0, :100].sum() == pytest.approx(100.0)
    assert frames[0, 100:].sum() == pytest.approx(0.0)


def test_frames_are_writable_copies():
    wav = np.arange(2000, dtype=np.float32)
    frames, _ = frame_signal(wav, 16000, frame_ms=30, hop_ms=10)
    frames[0, 0] = -999.0  # must not raise / must not alias wav
    assert wav[0] == 0.0


def test_bad_params_raise():
    with pytest.raises(ValueError):
        frame_signal(np.zeros(100), 16000, frame_ms=0, hop_ms=10)
