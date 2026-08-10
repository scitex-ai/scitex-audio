#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: src/scitex_audio/_stt_faster_whisper.py
"""faster-whisper (CTranslate2) speech-to-text backend.

The sibling of the whisper.cpp CLI backend in :mod:`scitex_audio._stt`.
Both produce the same result dict, so callers -- the ``transcribe-audio``
CLI verb and the ``audio_transcribe`` MCP tool -- do not care which ran.

Why this exists alongside whisper.cpp: CTranslate2 ships kernels for older
GPUs that the PyTorch wheels have dropped. Measured on a GTX 1070 (sm_61,
faster-whisper 1.2.1 / ctranslate2 4.8.1) with ``large-v3`` + ``int8``::

    cuda   load 5.05s   transcribe  1.46s
    cpu    load 2.93s   transcribe 21.60s     (~15x slower)

So the GPU is worth using on this card even though ``torch`` disagrees:
``torch.cuda.is_available()`` returns True there while ``get_arch_list()``
omits sm_61, i.e. torch claims a GPU it cannot actually run on. We never
ask torch -- CTranslate2 answers for itself, and it fails loudly
(requesting ``float16`` on Pascal raises rather than silently degrading).

This backend decodes through PyAV, so unlike the whisper.cpp path it does
NOT shell out to ``ffmpeg`` for non-WAV input.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

__all__ = [
    "COMPUTE_TYPE_ENV_VAR",
    "DEFAULT_COMPUTE_TYPE",
    "DEFAULT_MODEL",
    "DEVICE_ENV_VAR",
    "MODEL_ENV_VAR",
    "available",
    "format_timestamp",
    "resolve_device",
    "transcribe",
]

#: faster-whisper model id, or a path to a local snapshot directory.
DEFAULT_MODEL = "large-v3"

#: int8 measured fastest on Pascal and is the only quantised type
#: CTranslate2 offers there; float16 is unsupported on sm_61 and raises.
DEFAULT_COMPUTE_TYPE = "int8"

#: Override the model, e.g. "tiny" for interactive use, or a snapshot path.
MODEL_ENV_VAR = "SCITEX_AUDIO_FASTER_WHISPER_MODEL"

#: Force a device ("cuda" / "cpu"); unset means auto-detect.
DEVICE_ENV_VAR = "SCITEX_AUDIO_FASTER_WHISPER_DEVICE"

#: Override the compute type (e.g. "float32").
COMPUTE_TYPE_ENV_VAR = "SCITEX_AUDIO_FASTER_WHISPER_COMPUTE_TYPE"


def available() -> bool:
    """True if the faster-whisper package can be imported."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def resolve_device(device: Optional[str] = None) -> str:
    """Pick the compute device: explicit > environment > auto-detect.

    Auto-detect asks CTranslate2 whether it has a usable CUDA device. We
    deliberately do NOT consult ``torch``: on Pascal cards
    ``torch.cuda.is_available()`` reports True while the wheel ships no
    sm_61 kernel, so a torch-based check would promise a GPU that cannot run.
    """
    explicit = device or os.environ.get(DEVICE_ENV_VAR)
    if explicit:
        return explicit
    try:
        import ctranslate2

        return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    except Exception:
        # Unable to introspect means we cannot promise a GPU.
        return "cpu"


def format_timestamp(seconds: float) -> str:
    """Render seconds as ``HH:MM:SS.mmm``.

    faster-whisper reports float seconds while the whisper.cpp backend
    reports pre-formatted strings. Segments cross a published boundary --
    the MCP ``audio_transcribe`` tool returns them as JSON -- so both
    backends must agree on the shape, or switching backend silently
    changes that surface.
    """
    seconds = max(float(seconds), 0.0)
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def transcribe(
    audio_path: str,
    language: Optional[str] = "ja",
    model: Optional[str] = None,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
) -> dict:
    """Transcribe an audio file with faster-whisper.

    Returns the same dict shape as :func:`scitex_audio._stt.transcribe`:
    ``{success, text, segments, language, model, audio_path}`` on success,
    ``{success: False, error: ...}`` on failure.
    """
    resolved_path = str(Path(audio_path).resolve())
    if not Path(resolved_path).is_file():
        return {"success": False, "error": f"Audio file not found: {resolved_path}"}

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {
            "success": False,
            "error": (
                "faster-whisper is not installed. Install with: "
                "pip install 'scitex-audio[faster-whisper]'"
            ),
        }

    name = model or os.environ.get(MODEL_ENV_VAR) or DEFAULT_MODEL
    resolved_device = resolve_device(device)
    resolved_compute = (
        compute_type
        or os.environ.get(COMPUTE_TYPE_ENV_VAR)
        or DEFAULT_COMPUTE_TYPE
    )

    try:
        engine = WhisperModel(
            name, device=resolved_device, compute_type=resolved_compute
        )
    except Exception as exc:
        # Name the device/compute pair: the usual failure is an unsupported
        # combination (float16 on Pascal), and that pair is exactly what the
        # reader needs in order to fix it.
        return {
            "success": False,
            "error": (
                f"Failed to load faster-whisper model {name!r} on "
                f"device={resolved_device!r} compute_type={resolved_compute!r}: "
                f"{type(exc).__name__}: {exc}. "
                f"Override with {DEVICE_ENV_VAR} / {COMPUTE_TYPE_ENV_VAR}."
            ),
        }

    try:
        raw_segments, info = engine.transcribe(resolved_path, language=language)
        segments = [
            {
                "start": format_timestamp(segment.start),
                "end": format_timestamp(segment.end),
                "text": segment.text.strip(),
            }
            for segment in raw_segments
        ]
    except Exception as exc:
        return {
            "success": False,
            "error": (
                f"faster-whisper transcription failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }

    return {
        "success": True,
        "text": " ".join(s["text"] for s in segments).strip(),
        "segments": segments,
        # Report the language actually used: with language=None the model
        # detects one, and echoing the request back would be a lie.
        "language": getattr(info, "language", language) or language,
        "model": name,
        "audio_path": resolved_path,
    }


# EOF
