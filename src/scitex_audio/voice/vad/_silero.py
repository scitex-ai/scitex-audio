#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/vad/_silero.py

"""Silero VAD backend (SciTeX Voice V1 default).

Silero is a small, robust neural VAD that holds up in café noise far better
than an energy gate. torch is imported lazily so ``import
scitex_audio.voice`` stays dep-free; a clear hint fires on first use. Weights
are fetched once via torch.hub and cached locally (they never leave the
mesh — non-negotiable #1).

faster-whisper bundles Silero too; if the pipeline later standardises on
faster-whisper for ASR we reuse that copy instead of a second download. For
V1 this stays an independent, swappable backend.
"""

from __future__ import annotations

from typing import List

import numpy as np

from ._segment import Segment

__all__ = ["silero_vad"]

_INSTALL_HINT = (
    "Silero VAD needs torch. Install: pip install 'scitex-audio[voice]'. "
    "On the GTX 1070 (Pascal) use a torch<=2.7 cu12x wheel (2.8+ dropped "
    "sm_61). Or use backend='energy' for a zero-dependency fallback."
)

_MODEL_CACHE = {}


def _load_silero():
    if "model" in _MODEL_CACHE:
        return _MODEL_CACHE["model"], _MODEL_CACHE["utils"]
    try:
        import torch  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - exercised without dep
        raise RuntimeError(_INSTALL_HINT) from exc
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        trust_repo=True,
    )
    _MODEL_CACHE["model"] = model
    _MODEL_CACHE["utils"] = utils
    return model, utils


def silero_vad(
    wav: np.ndarray,
    sample_rate: int = 16000,
    min_speech_ms: float = 150.0,
) -> List[Segment]:
    """Return speech segments using the Silero neural VAD.

    Args:
        wav: 1-D mono waveform, float32.
        sample_rate: Must be 16000 (or 8000) for Silero.
        min_speech_ms: Minimum speech-run length to keep.

    Returns:
        List of ``Segment`` spans in samples.
    """
    import torch  # noqa: PLC0415

    model, utils = _load_silero()
    get_speech_timestamps = utils[0]
    tensor = torch.from_numpy(np.asarray(wav, dtype=np.float32).reshape(-1))
    stamps = get_speech_timestamps(
        tensor,
        model,
        sampling_rate=sample_rate,
        min_speech_duration_ms=int(min_speech_ms),
    )
    return [Segment(int(s["start"]), int(s["end"]), sample_rate) for s in stamps]


# EOF
