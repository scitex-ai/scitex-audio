#!/usr/bin/env python3
# Timestamp: "2026-03-26 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/_stt.py

"""
Speech-to-Text transcription using whisper.cpp.

Pipeline: audio file -> ffmpeg convert to WAV -> whisper-cli transcribe

Backends (discovery order):
    1. whisper-cli in PATH
    2. ~/.emacs.d/.cache/whisper.cpp/build/bin/whisper-cli
    3. Custom path via SCITEX_AUDIO_WHISPER_CLI env var

Models (discovery order):
    1. SCITEX_AUDIO_WHISPER_MODEL env var
    2. ~/.emacs.d/.cache/whisper.cpp/models/ggml-{model}.bin
    3. ~/.local/share/whisper-cli/ggml-{model}.bin
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

__all__ = [
    "BACKEND_ENV_VAR",
    "find_whisper_cli",
    "find_whisper_model",
    "resolve_backend",
    "transcribe",
]

# Default model — tiny is fast enough for interactive use
DEFAULT_MODEL = "tiny"

#: Pin the STT backend: "whisper.cpp", "faster-whisper", or "auto".
BACKEND_ENV_VAR = "SCITEX_AUDIO_STT_BACKEND"

#: Backend that has always served this module; still the default when both
#: are installed, so an existing working setup does not change under anyone.
BACKEND_WHISPER_CPP = "whisper.cpp"

#: Optional CTranslate2 backend — see :mod:`scitex_audio._stt_faster_whisper`.
BACKEND_FASTER_WHISPER = "faster-whisper"

BACKENDS = (BACKEND_WHISPER_CPP, BACKEND_FASTER_WHISPER)

# Model search directories
_MODEL_DIRS = [
    Path.home() / ".emacs.d" / ".cache" / "whisper.cpp" / "models",
    Path.home() / ".local" / "share" / "whisper-cli",
    Path.home() / ".local" / "share" / "whisper.cpp" / "models",
]

# whisper-cli search paths
_CLI_PATHS = [
    Path.home()
    / ".emacs.d"
    / ".cache"
    / "whisper.cpp"
    / "build"
    / "bin"
    / "whisper-cli",
]


def find_whisper_cli() -> Optional[str]:
    """Find whisper-cli binary.

    Returns
    -------
        Path to whisper-cli, or None if not found.
    """
    # 1. Environment variable override
    env_path = os.environ.get("SCITEX_AUDIO_WHISPER_CLI")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. PATH lookup
    which = shutil.which("whisper-cli")
    if which:
        return which

    # 3. Known locations
    for p in _CLI_PATHS:
        if p.is_file():
            return str(p)

    return None


def find_whisper_model(model: str = DEFAULT_MODEL) -> Optional[str]:
    """Find a whisper model file.

    Args:
        model: Model name (tiny, base, small, medium, large-v3-turbo, etc.)

    Returns
    -------
        Path to model file, or None if not found.
    """
    # 1. Environment variable override
    env_path = os.environ.get("SCITEX_AUDIO_WHISPER_MODEL")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. Search known directories
    filename = f"ggml-{model}.bin"
    for d in _MODEL_DIRS:
        candidate = d / filename
        if candidate.is_file():
            return str(candidate)

    return None


def available_models() -> list[str]:
    """List available whisper models.

    Returns
    -------
        List of model names (e.g., ["tiny", "base", "medium"]).
    """
    models = set()
    pattern = re.compile(r"^ggml-(.+)\.bin$")
    for d in _MODEL_DIRS:
        if d.is_dir():
            for f in d.iterdir():
                m = pattern.match(f.name)
                if m and not f.name.startswith("for-tests-"):
                    models.add(m.group(1))
    return sorted(models)


def _convert_to_wav(input_path: str, output_path: str) -> None:
    """Convert audio file to WAV format using ffmpeg.

    Args:
        input_path: Source audio file.
        output_path: Destination WAV file.

    Raises
    ------
        RuntimeError: If ffmpeg is not available or conversion fails.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found. Install with: sudo apt install ffmpeg")

    result = subprocess.run(
        [ffmpeg, "-y", "-i", input_path, output_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")


def _parse_whisper_output(stdout: str) -> list[dict]:
    """Parse whisper-cli output into segments.

    Args:
        stdout: Raw whisper-cli stdout.

    Returns
    -------
        List of dicts with keys: start, end, text.
    """
    segments = []
    pattern = re.compile(
        r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\]\s*(.*)"
    )
    for line in stdout.strip().splitlines():
        m = pattern.match(line.strip())
        if m:
            segments.append(
                {
                    "start": m.group(1),
                    "end": m.group(2),
                    "text": m.group(3).strip(),
                }
            )
    return segments


def _whisper_cpp_usable(
    whisper_cli: Optional[str] = None, model: str = DEFAULT_MODEL
) -> bool:
    """True if both the whisper.cpp binary and a model file are present."""
    return bool(
        (whisper_cli or find_whisper_cli()) and find_whisper_model(model)
    )


def resolve_backend(
    backend: Optional[str] = None,
    whisper_cli: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Choose the STT backend: explicit > environment > auto-detect.

    Auto-detect prefers whisper.cpp *when it is actually set up* -- its
    binary and a model file both resolve -- because that means someone
    deliberately installed it, and silently switching engines under a
    working setup would change transcripts for no reason they asked for.
    Otherwise it falls back to faster-whisper.

    Returns a name from :data:`BACKENDS`; an unknown explicit value is
    returned unchanged so the caller can report it rather than guessing.
    """
    explicit = backend or os.environ.get(BACKEND_ENV_VAR)
    if explicit and explicit != "auto":
        return explicit
    if _whisper_cpp_usable(whisper_cli, model):
        return BACKEND_WHISPER_CPP
    from . import _stt_faster_whisper

    if _stt_faster_whisper.available():
        return BACKEND_FASTER_WHISPER
    # Neither is usable; name whisper.cpp so the existing, more detailed
    # "not found" errors below explain how to install it.
    return BACKEND_WHISPER_CPP


def transcribe(
    audio_path: str,
    language: Optional[str] = "ja",
    model: Optional[str] = None,
    whisper_cli: Optional[str] = None,
    model_path: Optional[str] = None,
    backend: Optional[str] = None,
) -> dict:
    """Transcribe an audio file to text.

    Dispatches to whisper.cpp (default when installed) or faster-whisper.
    Both backends return the same dict shape.

    Args:
        audio_path: Path to audio file (any format ffmpeg supports).
        language: Language code (e.g., "ja", "en"). None for auto-detect.
        model: Model name. Defaults per backend ("tiny" for whisper.cpp,
            "large-v3" for faster-whisper) since their model names differ.
        whisper_cli: Override path to whisper-cli binary (whisper.cpp only).
        model_path: Override path to model file (whisper.cpp only).
        backend: "whisper.cpp", "faster-whisper", or "auto" (default).

    Returns
    -------
        Dict with keys: success, text, segments, language, model, audio_path.
    """
    chosen = resolve_backend(backend, whisper_cli, model or DEFAULT_MODEL)

    if chosen == BACKEND_FASTER_WHISPER:
        from . import _stt_faster_whisper

        return _stt_faster_whisper.transcribe(
            audio_path, language=language, model=model
        )

    if chosen != BACKEND_WHISPER_CPP:
        return {
            "success": False,
            "error": (
                f"Unknown STT backend {chosen!r}. "
                f"Choose one of: {', '.join(BACKENDS)}, or 'auto'."
            ),
        }

    return _transcribe_whisper_cpp(
        audio_path,
        language=language,
        model=model or DEFAULT_MODEL,
        whisper_cli=whisper_cli,
        model_path=model_path,
    )


def _transcribe_whisper_cpp(
    audio_path: str,
    language: Optional[str] = "ja",
    model: str = DEFAULT_MODEL,
    whisper_cli: Optional[str] = None,
    model_path: Optional[str] = None,
) -> dict:
    """Transcribe audio file to text using whisper.cpp.

    Args:
        audio_path: Path to audio file (any format ffmpeg supports).
        language: Language code (e.g., "ja", "en"). None for auto-detect.
        model: Whisper model name (tiny, base, small, medium, large-v3-turbo).
        whisper_cli: Override path to whisper-cli binary.
        model_path: Override path to model file.

    Returns
    -------
        Dict with keys: success, text, segments, language, model, audio_path.
    """
    audio_path = str(Path(audio_path).resolve())

    # Find whisper-cli
    cli = whisper_cli or find_whisper_cli()
    if not cli:
        return {
            "success": False,
            "error": (
                "whisper-cli not found. Install whisper.cpp or set "
                "SCITEX_AUDIO_WHISPER_CLI environment variable."
            ),
        }

    # Find model
    mdl = model_path or find_whisper_model(model)
    if not mdl:
        return {
            "success": False,
            "error": (
                f"Whisper model '{model}' not found. Download with: "
                f"cd ~/.emacs.d/.cache/whisper.cpp/models && "
                f"bash download-ggml-model.sh {model}"
            ),
        }

    # Convert to WAV if needed
    wav_path = audio_path
    tmp_wav = None
    if not audio_path.lower().endswith(".wav"):
        fd, tmp_wav = tempfile.mkstemp(suffix=".wav", prefix="scitex_stt_")
        os.close(fd)
        wav_path = tmp_wav
        try:
            _convert_to_wav(audio_path, wav_path)
        except RuntimeError as e:
            if tmp_wav:
                _safe_unlink(tmp_wav)
            return {"success": False, "error": str(e)}

    try:
        # Build whisper-cli command
        cmd = [cli, "-m", mdl, "-f", wav_path]
        if language:
            cmd.extend(["-l", language])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"whisper-cli failed (exit {result.returncode}): {result.stderr}",
            }

        # Parse output
        segments = _parse_whisper_output(result.stdout)
        full_text = " ".join(s["text"] for s in segments)

        return {
            "success": True,
            "text": full_text,
            "segments": segments,
            "language": language,
            "model": model,
            "audio_path": audio_path,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Transcription timed out (120s limit)",
        }
    finally:
        if tmp_wav:
            _safe_unlink(tmp_wav)


def _safe_unlink(path: str) -> None:
    """Remove file, ignoring errors."""
    try:
        os.unlink(path)
    except Exception:
        pass


# EOF
