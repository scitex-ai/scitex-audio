#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/io/_wav.py

"""Read/write mono 16 kHz waveforms for SciTeX Voice V1.

The verifier and ECAPA both want mono float32 @ 16 kHz. This module reads
audio to that canonical form and writes it back. soundfile is imported
lazily so ``import scitex_audio.voice`` works without it; a clear install
hint fires on first use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np

__all__ = ["TARGET_SR", "read_wav", "write_wav", "to_mono"]

TARGET_SR = 16000

_INSTALL_HINT = (
    "voice io needs soundfile. Install: pip install 'scitex-audio[voice]' "
    "(or: pip install soundfile)."
)


def _soundfile():
    try:
        import soundfile as sf  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - exercised without dep
        raise RuntimeError(_INSTALL_HINT) from exc
    return sf


def to_mono(wav: np.ndarray) -> np.ndarray:
    """Collapse a (n,) or (n, channels) array to mono float32 (n,)."""
    arr = np.asarray(wav, dtype=np.float32)
    if arr.ndim == 2:
        arr = arr.mean(axis=1)
    return arr.reshape(-1).astype(np.float32)


def read_wav(path: str | Path) -> Tuple[np.ndarray, int]:
    """Read an audio file to mono float32 and its native sample rate.

    Resampling to 16 kHz is intentionally NOT done here — that needs a real
    resampler (soundfile/torchaudio/ffmpeg) and is handled at capture time
    on the Windows client, which already emits 16 kHz mono. This returns the
    file as-is (mono) so callers can assert the rate.

    Args:
        path: Audio file path (WAV/FLAC/OGG — whatever libsndfile supports).

    Returns:
        ``(wav, sample_rate)`` with ``wav`` mono float32.
    """
    sf = _soundfile()
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    return to_mono(data), int(sr)


def write_wav(path: str | Path, wav: np.ndarray, sample_rate: int = TARGET_SR) -> None:
    """Write a mono float32 waveform to a WAV file.

    Args:
        path: Destination path.
        wav: 1-D mono waveform.
        sample_rate: Sample rate to stamp (default 16 kHz).
    """
    sf = _soundfile()
    sf.write(str(path), to_mono(wav), int(sample_rate), subtype="PCM_16")


# EOF
