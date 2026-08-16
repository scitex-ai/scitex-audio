#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/tests/scitex_audio/voice/test__wav.py

"""Tests for scitex_audio.voice.io._wav (SciTeX Voice V1).

The read/write roundtrip needs libsndfile (soundfile); skipped if absent.
``to_mono`` is pure-numpy and always tested.
"""

from __future__ import annotations

import numpy as np
import pytest

from scitex_audio.voice.io import TARGET_SR, to_mono


def test_to_mono_from_stereo():
    stereo = np.array([[1.0, 3.0], [2.0, 4.0]], dtype=np.float32)
    mono = to_mono(stereo)
    assert mono.shape == (2,)
    assert mono[0] == pytest.approx(2.0)  # (1+3)/2
    assert mono[1] == pytest.approx(3.0)  # (2+4)/2


def test_to_mono_passthrough_1d():
    mono = to_mono(np.array([0.1, 0.2, 0.3], dtype=np.float32))
    assert mono.shape == (3,)


def test_wav_roundtrip(tmp_path):
    pytest.importorskip("soundfile")
    from scitex_audio.voice.io import read_wav, write_wav

    sr = TARGET_SR
    t = np.arange(sr, dtype=np.float32) / sr
    wav = (0.3 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)
    path = tmp_path / "tone.wav"
    write_wav(path, wav, sr)

    back, back_sr = read_wav(path)
    assert back_sr == sr
    assert back.shape == wav.shape
    # PCM_16 quantisation tolerance.
    assert np.max(np.abs(back - wav)) < 1e-3
