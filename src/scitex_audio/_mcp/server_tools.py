#!/usr/bin/env python3
# Timestamp: "2026-05-24 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/_mcp/server_tools.py

"""MCP tool bodies for the scitex-audio FastMCP server.

Plain module-level functions so they are importable and testable
without ``fastmcp`` installed. ``mcp_server.py`` registers each of
these under a ``@mcp.tool()`` wrapper whose name matches its public
``scitex_audio`` Python counterpart (audit-mcp-tools §6 parity):

    audio_available_backends        -> scitex_audio.available_backends
    audio_check_wsl_audio           -> scitex_audio.check_wsl_audio
    audio_check_local_audio_available -> scitex_audio.check_local_audio_available
    audio_stop_speech               -> scitex_audio.stop_speech
    audio_generate_bytes            -> scitex_audio.generate_bytes
    audio_announce_context          -> scitex_audio.announce_context

Every body delegates to the matching public API and returns a JSON
string envelope. Injectable seams (``*_fn=`` / ``audio_dir=``) let
tests pass small hand-rolled fakes — no mocks.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

__all__ = [
    "available_backends_tool",
    "check_wsl_audio_tool",
    "check_local_audio_available_tool",
    "stop_speech_tool",
    "generate_bytes_tool",
    "announce_context_tool",
]


def available_backends_tool(available_fn=None, fallback_order=None) -> str:
    """List available TTS backends and their status.

    Mirrors :func:`scitex_audio.available_backends`.

    Args:
        available_fn: Injectable backend lister (testing). Defaults to
            ``scitex_audio.available_backends``.
        fallback_order: Injectable fallback order (testing). Defaults to
            ``scitex_audio.FALLBACK_ORDER``.

    Returns:
        JSON string with available backends and fallback order.
    """
    try:
        if available_fn is None or fallback_order is None:
            from .. import FALLBACK_ORDER, available_backends

            if available_fn is None:
                available_fn = available_backends
            if fallback_order is None:
                fallback_order = FALLBACK_ORDER
        return json.dumps(
            {
                "success": True,
                "available": available_fn(),
                "fallback_order": list(fallback_order),
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def check_wsl_audio_tool(status_fn=None) -> str:
    """Check WSL audio connectivity and available playback methods.

    Mirrors :func:`scitex_audio.check_wsl_audio`.

    Args:
        status_fn: Injectable status probe (testing). Defaults to
            ``scitex_audio.check_wsl_audio``.

    Returns:
        JSON string with audio status information.
    """
    try:
        if status_fn is None:
            from .. import check_wsl_audio as status_fn
        status = status_fn()
        status["success"] = True
        status["timestamp"] = datetime.now().isoformat()
        return json.dumps(status, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def check_local_audio_available_tool(check_fn=None) -> str:
    """Check whether local audio playback is usable on this host.

    Mirrors :func:`scitex_audio.check_local_audio_available`.

    Args:
        check_fn: Injectable availability probe (testing). Defaults to
            ``scitex_audio.check_local_audio_available``.

    Returns:
        JSON string with the local-audio availability report.
    """
    try:
        if check_fn is None:
            from .. import check_local_audio_available as check_fn
        status = check_fn()
        status["success"] = True
        status["timestamp"] = datetime.now().isoformat()
        return json.dumps(status, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def stop_speech_tool(stop_fn=None) -> str:
    """Stop any currently playing speech.

    Mirrors :func:`scitex_audio.stop_speech`.

    Args:
        stop_fn: Injectable stopper (testing). Defaults to
            ``scitex_audio.stop_speech``.

    Returns:
        JSON string confirming the stop request.
    """
    try:
        if stop_fn is None:
            from .. import stop_speech as stop_fn
        stop_fn()
        return json.dumps(
            {
                "success": True,
                "stopped": True,
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def generate_bytes_tool(
    text: str,
    backend: Optional[str] = None,
    voice: Optional[str] = None,
    output_path: Optional[str] = None,
    generate_fn=None,
    audio_dir=None,
) -> str:
    """Generate TTS audio to a file without playing it.

    Mirrors :func:`scitex_audio.generate_bytes`. Raw bytes don't travel
    well over MCP/JSON, so this writes the bytes to a file and returns
    the path + size.

    Args:
        text: Text to synthesize.
        backend: TTS backend (None -> fallback chain).
        voice: Voice/language override.
        output_path: Explicit output file (None -> timestamped file in
            the audio runtime dir).
        generate_fn: Injectable byte generator (testing). Defaults to
            ``scitex_audio.generate_bytes``.
        audio_dir: Injectable output directory (testing). Defaults to
            the audio runtime dir.

    Returns:
        JSON string with the written path and byte count.
    """
    try:
        if generate_fn is None:
            from .. import generate_bytes as generate_fn
        audio = generate_fn(text, backend=backend, voice=voice)
        if output_path is None:
            if audio_dir is None:
                from ..mcp_server import _get_audio_dir

                audio_dir = _get_audio_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(Path(audio_dir) / f"tts_{timestamp}.mp3")
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(audio)
        return json.dumps(
            {
                "success": True,
                "path": str(out),
                "bytes": len(audio),
                "backend": backend,
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def announce_context_tool(
    include_full_path: bool = False,
    announce_fn=None,
) -> str:
    """Announce the current working directory and git branch over audio.

    Mirrors :func:`scitex_audio.announce_context`.

    Args:
        include_full_path: Include the absolute path instead of the
            directory name.
        announce_fn: Injectable announce function (testing). Defaults to
            ``scitex_audio.announce_context``.

    Returns:
        JSON string with the orientation context and speak status.
    """
    try:
        if announce_fn is None:
            from .. import announce_context as announce_fn
        result = announce_fn(include_full_path=include_full_path)
        result["success"] = True
        result["timestamp"] = datetime.now().isoformat()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# EOF
