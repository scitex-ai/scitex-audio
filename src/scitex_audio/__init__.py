#!/usr/bin/env python3
# Timestamp: "2026-03-14 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/__init__.py
"""
SciTeX Audio - Text-to-Speech with Multiple Backends

Backends (fallback order):
    - elevenlabs: ElevenLabs (paid, high quality, speed=1.2)
    - luxtts: LuxTTS (open-source, offline, voice-cloning, speed=2.0)
    - gtts: Google TTS (free, requires internet, speed=1.5)
    - pyttsx3: System TTS (offline, free, uses espeak/SAPI5)

Usage:
    from scitex_audio import speak
    speak("Hello, world!")

    from scitex_audio import get_tts, LuxTTS
    tts = get_tts("luxtts")
    tts.speak("Hello!")
"""

from __future__ import annotations as _annotations

import subprocess as _subprocess

try:
    from importlib.metadata import version as _v, PackageNotFoundError
    try:
        __version__ = _v("scitex-audio")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"
# Import from engines subpackage (hide module from dir())
from ._engines import ElevenLabsTTS, GoogleTTS, LuxTTS, SystemTTS
from ._engines._base import BaseTTS as _BaseTTS
from ._engines._base import TTSBackend as _TTSBackend


def stop_speech() -> None:
    """Stop any currently playing speech by killing espeak processes."""
    try:
        _subprocess.run(["pkill", "-9", "espeak"], capture_output=True)
    except Exception:
        pass


def check_wsl_audio() -> dict:
    """Check WSL audio status and connectivity."""
    import os
    import shutil

    result = {
        "is_wsl": False,
        "wslg_available": False,
        "pulse_server_exists": False,
        "pulse_connected": False,
        "windows_fallback_available": False,
        "recommended": "linux",
    }

    if os.path.exists("/mnt/c/Windows"):
        result["is_wsl"] = True
        if os.path.exists("/mnt/wslg"):
            result["wslg_available"] = True
        if os.path.exists("/mnt/wslg/PulseServer"):
            result["pulse_server_exists"] = True
            try:
                env = os.environ.copy()
                env["PULSE_SERVER"] = "unix:/mnt/wslg/PulseServer"
                proc = _subprocess.run(
                    ["pactl", "info"],
                    capture_output=True,
                    timeout=5,
                    env=env,
                )
                if proc.returncode == 0:
                    result["pulse_connected"] = True
            except Exception:
                pass
        if shutil.which("powershell.exe"):
            result["windows_fallback_available"] = True
        if result["pulse_connected"]:
            result["recommended"] = "linux"
        elif result["windows_fallback_available"]:
            result["recommended"] = "windows"
        else:
            result["recommended"] = "none"
    else:
        result["recommended"] = "linux"

    return result


from ._audio_check import check_local_audio_available
from ._env_registry import generate_template as generate_env_template
from ._stt import available_models, find_whisper_cli, find_whisper_model, transcribe
from ._tts import TTS

__all__ = [
    "__version__",
    # Core
    "speak",
    "generate_bytes",
    "stop_speech",
    "get_tts",
    "available_backends",
    # Engine classes
    "TTS",
    "GoogleTTS",
    "ElevenLabsTTS",
    "SystemTTS",
    "LuxTTS",
    # Diagnostics
    "check_wsl_audio",
    "check_local_audio_available",
    # Configuration
    "generate_env_template",
    # STT (Speech-to-Text)
    "transcribe",
    "find_whisper_cli",
    "find_whisper_model",
    "available_models",
]

FALLBACK_ORDER = ["elevenlabs", "luxtts", "gtts", "pyttsx3"]


def available_backends() -> list[str]:
    """Return list of available TTS backends."""
    backends = []

    if SystemTTS:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.stop()
            backends.append("pyttsx3")
        except Exception:
            pass

    if GoogleTTS:
        backends.append("gtts")

    if LuxTTS:
        try:
            import zipvoice  # noqa: F401

            backends.append("luxtts")
        except ImportError:
            pass

    if ElevenLabsTTS:
        import os

        api_key = os.environ.get("SCITEX_AUDIO_ELEVENLABS_API_KEY") or os.environ.get(
            "ELEVENLABS_API_KEY"
        )
        if api_key:
            backends.append("elevenlabs")

    return backends


def get_tts(backend: str | None = None, **kwargs) -> _BaseTTS:
    """Get a TTS instance for the specified backend."""
    backends = available_backends()

    if not backends:
        raise ValueError(
            "No TTS backends available. Install one of:\n"
            "  pip install pyttsx3       # System TTS (offline, free)\n"
            "  pip install gTTS          # Google TTS (free, needs internet)\n"
            "  pip install scitex-audio[luxtts]  # LuxTTS (open-source, offline)\n"
            "  pip install elevenlabs    # ElevenLabs (paid, best quality)"
        )

    if backend is None:
        for b in FALLBACK_ORDER:
            if b in backends:
                backend = b
                break

    if backend == "pyttsx3" and SystemTTS and "pyttsx3" in backends:
        return SystemTTS(**kwargs)
    elif backend == "gtts" and GoogleTTS:
        return GoogleTTS(**kwargs)
    elif backend == "elevenlabs" and ElevenLabsTTS:
        return ElevenLabsTTS(**kwargs)
    elif backend == "luxtts" and LuxTTS:
        return LuxTTS(**kwargs)
    else:
        raise ValueError(f"Backend '{backend}' not available. Available: {backends}")


from ._speak import speak


def generate_bytes(
    text: str,
    backend: str | None = None,
    voice: str | None = None,
    **kwargs,
) -> bytes:
    """Generate TTS audio as raw bytes without playing."""
    tts = get_tts(backend, **kwargs)
    return tts.to_bytes(text, voice=voice)


# EOF
