#!/usr/bin/env python3
"""Main speak() function with smart local/remote routing.

This module provides the primary speak() function that intelligently
routes audio to local or relay based on availability.
"""

from __future__ import annotations

import os
from typing import Callable, Optional

__all__ = [
    "speak",
    "_speak_local",
    "_try_speak_with_fallback",
    "_resolve_preferred_backend",
    "_degradation_notice",
]

# Env var: the operator's preferred default TTS backend. Set it in
# ``~/.scitex/audio/local.src`` (loaded via SCITEX_AUDIO_ENV_SRC). When unset,
# the first available entry of FALLBACK_ORDER wins.
_PREFERRED_ENV = "SCITEX_AUDIO_DEFAULT_BACKEND"


def _resolve_preferred_backend(available: list, order: list) -> Optional[str]:
    """Return the backend the operator EXPECTS to hear.

    Precedence: ``$SCITEX_AUDIO_DEFAULT_BACKEND`` (if available) -> first
    entry of ``order`` that is available -> None. This is the baseline the
    loud-fallback logic compares the actually-used backend against.
    """
    pref = (os.environ.get(_PREFERRED_ENV) or "").strip()
    if pref and pref in available:
        return pref
    for b in order:
        if b in available:
            return b
    return None


def _degradation_notice(preferred: Optional[str], used: str) -> str:
    """Spoken prefix announcing a fallback to a worse voice (fail-loud).

    Empty string when ``used`` IS the preferred backend (no degradation).
    Otherwise a short sentence the degraded backend itself speaks, so the
    operator audibly realises the voice dropped and why — no silent fallback.
    """
    if not preferred or used == preferred:
        return ""
    return f"Voice degraded: {preferred} unavailable, using {used}. "


def _try_speak_with_fallback(
    text: str,
    voice: Optional[str] = None,
    play: bool = True,
    output_path: Optional[str] = None,
    backends: Optional[list] = None,
    order: Optional[list] = None,
    tts_factory: Optional[Callable] = None,
    **kwargs,
) -> tuple:
    """Try to speak with fallback through backends — loud on degradation.

    Tries the operator's preferred backend first, then the remaining
    ``order``. If the backend that succeeds is NOT the preferred one, a
    spoken :func:`_degradation_notice` is prepended so the drop is audible
    (fail-loud, no silent fallback), and the result carries ``degraded=True``
    + ``preferred_backend``.

    ``backends`` / ``order`` / ``tts_factory`` are injection seams (default to
    the real ``available_backends`` / ``FALLBACK_ORDER`` / ``get_tts``) so the
    routing + degradation logic is unit-testable without real engines.

    Returns ``(result_dict, backend_used, error_log)``.
    """
    if backends is None or order is None or tts_factory is None:
        from . import FALLBACK_ORDER, available_backends, get_tts

        backends = available_backends() if backends is None else backends
        order = FALLBACK_ORDER if order is None else order
        tts_factory = get_tts if tts_factory is None else tts_factory

    preferred = _resolve_preferred_backend(backends, order)
    # Try preferred first, then the rest of the order (availability-filtered).
    seq = [preferred] if preferred else []
    seq += [b for b in order if b in backends and b != preferred]

    errors = []
    for backend in seq:
        if backend not in backends:
            continue
        try:
            tts = tts_factory(backend, **kwargs)
            spoken = _degradation_notice(preferred, backend) + text
            result = tts.speak(
                text=spoken,
                voice=voice,
                play=play,
                output_path=output_path,
            )
            result["backend"] = backend
            result["preferred_backend"] = preferred
            result["degraded"] = bool(preferred and backend != preferred)
            return (result, backend, errors)
        except Exception as e:
            errors.append(f"{backend}: {str(e)}")
            continue

    return (None, None, errors)


def _speak_local(
    text: str,
    backend: Optional[str] = None,
    voice: Optional[str] = None,
    play: bool = True,
    output_path: Optional[str] = None,
    fallback: bool = True,
    **kwargs,
) -> dict:
    """Local TTS playback (original implementation).

    Returns:
        Dict with keys: success, played, play_requested, backend, path (optional).
    """
    from . import get_tts

    # If specific backend requested without fallback
    if backend and not fallback:
        tts = get_tts(backend, **kwargs)
        result = tts.speak(text=text, voice=voice, play=play, output_path=output_path)
        result["backend"] = backend
        return result

    # Use fallback logic
    if fallback and backend is None:
        result, used_backend, errors = _try_speak_with_fallback(
            text=text, voice=voice, play=play, output_path=output_path, **kwargs
        )
        if result is None and errors:
            raise RuntimeError("All TTS backends failed:\n" + "\n".join(errors))
        return (
            result if result else {"success": False, "played": False, "errors": errors}
        )

    # Specific backend with fallback enabled
    try:
        tts = get_tts(backend, **kwargs)
        result = tts.speak(text=text, voice=voice, play=play, output_path=output_path)
        result["backend"] = backend
        return result
    except Exception as e:
        if fallback:
            result, used_backend, errors = _try_speak_with_fallback(
                text=text, voice=voice, play=play, output_path=output_path, **kwargs
            )
            if result is None:
                raise RuntimeError(
                    f"Primary backend '{backend}' failed: {e}\n"
                    f"Fallback errors:\n" + "\n".join(errors)
                )
            return result
        raise


def speak(
    text: str,
    backend: Optional[str] = None,
    voice: Optional[str] = None,
    play: bool = True,
    output_path: Optional[str] = None,
    fallback: Optional[bool] = None,
    rate: Optional[int] = None,
    speed: Optional[float] = None,
    mode: Optional[str] = None,
    **kwargs,
) -> dict:
    """Convert text to speech with smart local/remote switching.

    Modes:
        - local: Always use local TTS backends (fails if audio unavailable)
        - remote: Always forward to relay server
        - auto: Smart routing - prefers relay if local audio unavailable

    Smart Routing (auto mode):
        1. Checks if local audio sink is available (not SUSPENDED)
        2. If local unavailable and relay configured, uses relay
        3. If both unavailable, returns error with clear message

    Fallback order (local, only when backend is None): elevenlabs -> luxtts -> gtts -> pyttsx3

    Args:
        text: Text to speak.
        backend: TTS backend ('elevenlabs', 'luxtts', 'gtts', 'pyttsx3').
                 Auto-selects with fallback if None.
        voice: Voice name, ID, or language code.
        play: Whether to play the audio.
        output_path: Path to save audio file.
        fallback: If None (default), True when backend is None, False when backend is
                  explicitly specified — i.e. an explicit backend request fails loud
                  rather than silently falling back. Pass True/False to override.
        rate: Speech rate in words per minute (pyttsx3 only, default 150).
        speed: Speed multiplier for gtts (1.0=normal, >1.0=faster, <1.0=slower).
        mode: Override mode ('local', 'remote', 'auto'). Uses env if None.
        **kwargs: Additional backend options.

    Returns:
        Dict with: success, played, play_requested, backend, path (if saved), mode.

    Environment Variables:
        SCITEX_AUDIO_MODE: Default mode ('local', 'remote', 'auto')
        SCITEX_AUDIO_RELAY_URL: Relay server URL for remote mode
    """
    from ._audio_check import check_local_audio_available
    from ._branding import get_mode, get_relay_url
    from ._relay import is_relay_available, relay_speak

    # Remove rate/speed from kwargs to avoid duplicate passing
    kwargs.pop("rate", None)
    kwargs.pop("speed", None)

    # Resolve fallback default: explicit backend => no silent fallback (no-fallbacks policy)
    if fallback is None:
        fallback = backend is None

    # Determine mode
    effective_mode = mode or get_mode()

    # Remote mode: always use relay
    if effective_mode == "remote":
        relay_url = get_relay_url()
        if not relay_url:
            return {
                "success": False,
                "played": False,
                "play_requested": play,
                "mode": "remote",
                "error": "SCITEX_AUDIO_RELAY_URL or SCITEX_AUDIO_RELAY_HOST not set",
            }
        result = relay_speak(
            text=text,
            backend=backend,
            voice=voice,
            rate=rate or 150,
            speed=speed or 1.5,
            play=play,
            **kwargs,
        )
        return {
            "success": result.get("success", False),
            "played": result.get("success", False) and play,
            "play_requested": play,
            "mode": "remote",
            "path": result.get("saved_to"),
        }

    # Auto mode: smart routing based on local audio availability
    if effective_mode == "auto":
        # Check local audio availability when playback requested
        local_audio_ok = True
        local_audio_info = None
        if play:
            local_audio_info = check_local_audio_available()
            local_audio_ok = local_audio_info.get("available", True)

        relay_url = get_relay_url()
        relay_ok = relay_url and is_relay_available()

        # Smart routing: prefer relay if local audio unavailable
        if not local_audio_ok and relay_ok:
            try:
                result = relay_speak(
                    text=text,
                    backend=backend,
                    voice=voice,
                    rate=rate or 150,
                    speed=speed or 1.5,
                    play=play,
                    **kwargs,
                )
                if result.get("success"):
                    return {
                        "success": True,
                        "played": play,
                        "play_requested": play,
                        "mode": "remote",
                        "path": result.get("saved_to"),
                        "routing": f"relay (local: {local_audio_info.get('reason')})",
                    }
            except Exception:
                pass  # Fall through to local

        elif relay_ok:
            # Both available, try relay first
            try:
                result = relay_speak(
                    text=text,
                    backend=backend,
                    voice=voice,
                    rate=rate or 150,
                    speed=speed or 1.5,
                    play=play,
                    **kwargs,
                )
                if result.get("success"):
                    return {
                        "success": True,
                        "played": play,
                        "play_requested": play,
                        "mode": "remote",
                        "path": result.get("saved_to"),
                    }
            except Exception:
                pass  # Fall through to local

        # Local unavailable and no relay = failure
        if not local_audio_ok and not relay_ok:
            return {
                "success": False,
                "played": False,
                "play_requested": play,
                "mode": "local",
                "error": f"Audio unavailable: {local_audio_info.get('reason')}",
                "local_state": local_audio_info.get("state"),
                "relay_configured": relay_url is not None,
            }

    # Local mode (explicit or fallback from auto)
    if effective_mode == "local" and play:
        local_audio_info = check_local_audio_available()
        if not local_audio_info.get("available", True):
            return {
                "success": False,
                "played": False,
                "play_requested": play,
                "mode": "local",
                "error": f"Local audio unavailable: {local_audio_info.get('reason')}",
                "local_state": local_audio_info.get("state"),
            }

    result = _speak_local(
        text=text,
        backend=backend,
        voice=voice,
        play=play,
        output_path=output_path,
        fallback=fallback,
        **kwargs,
    )
    result["mode"] = "local"
    return result


# EOF
