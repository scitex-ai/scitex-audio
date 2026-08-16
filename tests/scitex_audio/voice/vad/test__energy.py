#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/vad/test__energy.py

"""Tests for the pure-numpy energy VAD + the segment_speech dispatcher."""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.vad import energy_vad, segment_speech


def _tone(n, sr=16000, freq=200.0, amp=0.5):
    """A mono sine tone of ``n`` samples — a stand-in for voiced speech."""
    t = np.arange(n, dtype=np.float32) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _speech_in_silence(sr=16000):
    """1 s tone flanked by 0.5 s silence either side."""
    pad = np.zeros(sr // 2, dtype=np.float32)
    return np.concatenate([pad, _tone(sr, sr), pad])


def test_energy_vad_finds_single_speech_segment():
    # Arrange
    wav = _speech_in_silence()

    # Act
    segs = energy_vad(wav, 16000, threshold_db=-40.0, min_speech_ms=150.0)

    # Assert
    assert len(segs) == 1


def test_energy_vad_locates_speech_onset():
    # Arrange
    wav = _speech_in_silence()

    # Act
    segs = energy_vad(wav, 16000, threshold_db=-40.0, min_speech_ms=150.0)

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
