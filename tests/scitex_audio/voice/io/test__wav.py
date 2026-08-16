#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__wav.py

"""Tests for scitex_audio.voice.io._wav (SciTeX Voice V1).

The read/write roundtrip needs libsndfile (soundfile); guarded with
importorskip. ``to_mono`` is pure-numpy and always tested.
"""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.io import TARGET_SR, to_mono


def test_to_mono_from_stereo_returns_mono_shape():
    # Arrange
    stereo = np.array([[1.0, 3.0], [2.0, 4.0]], dtype=np.float32)

    # Act
    mono = to_mono(stereo)

    # Assert
    assert mono.shape == (2,)


def test_to_mono_averages_stereo_channels():
    # Arrange
    stereo = np.array([[1.0, 3.0], [2.0, 4.0]], dtype=np.float32)

    # Act
    mono = to_mono(stereo)

    # Assert
    assert mono[0] == pytest.approx(2.0)  # (1 + 3) / 2


def test_to_mono_passes_through_mono_input():
    # Arrange
    signal = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    # Act
    mono = to_mono(signal)

    # Assert
    assert mono.shape == (3,)


@pytest.fixture
def wav_roundtrip(tmp_path):
    """Write a 16 kHz mono tone and read it back; yields (orig, back, sr)."""
    pytest.importorskip("soundfile")
    from scitex_audio.voice.io import read_wav, write_wav

    sr = TARGET_SR
    t = np.arange(sr, dtype=np.float32) / sr
    orig = (0.3 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)
    path = tmp_path / "tone.wav"
    write_wav(path, orig, sr)
    back, back_sr = read_wav(path)
    return orig, back, back_sr


def test_wav_roundtrip_preserves_sample_rate(wav_roundtrip):
    # Arrange
    _orig, _back, back_sr = wav_roundtrip

    # Act
    result = back_sr

    # Assert
    assert result == TARGET_SR


def test_wav_roundtrip_preserves_shape(wav_roundtrip):
    # Arrange
    orig, back, _sr = wav_roundtrip

    # Act
    result = back.shape

    # Assert
    assert result == orig.shape


def test_wav_roundtrip_preserves_samples_within_pcm16_tolerance(wav_roundtrip):
    # Arrange
    orig, back, _sr = wav_roundtrip

    # Act
    max_err = float(np.max(np.abs(back - orig)))

    # Assert
    assert max_err < 1e-3
