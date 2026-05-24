#!/usr/bin/env python3
# Timestamp: "2026-05-19 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-audio/src/scitex_audio/_state_paths.py

"""
On-disk layout for scitex-audio state.

The operator's dotfiles repo tracks ``~/.scitex/audio/`` as a whole, with
``runtime/`` as the single carve-out for ephemeral, untracked artifacts.
Every file that scitex-audio writes at runtime — TTS outputs, IPC lock
files, transient caches — MUST land under ``~/.scitex/audio/runtime/``.

Public, named helpers live here so the on-disk layout has exactly one
source of truth. Callers that previously rolled their own
``_get_audio_dir()`` should delegate to the named helper below.

Layout::

    ~/.scitex/audio/                       # operator-tracked
    ├── local.src, remote.src              # env-source files (tracked)
    ├── reference/                         # voice-cloning refs (tracked)
    └── runtime/                           # untracked carve-out
        ├── tts/                           # generated TTS outputs (mp3/wav)
        ├── locks/                         # IPC lock files
        ├── cache/                         # transient caches
        └── completion/                    # shell completion (existing)
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "audio_state_base",
    "audio_runtime_dir",
    "tts_output_dir",
    "lock_dir",
    "audio_playback_lock_path",
    "cache_dir",
]


def audio_state_base() -> Path:
    """Return ``~/.scitex/audio/`` (or ``$SCITEX_DIR/audio/``).

    This is the *tracked* root; do not write ephemeral artifacts directly
    here — use one of the ``runtime/<category>/`` helpers below.
    """
    base = Path(os.getenv("SCITEX_DIR", Path.home() / ".scitex"))
    return base / "audio"


def audio_runtime_dir() -> Path:
    """Return ``~/.scitex/audio/runtime/`` (created on demand).

    The only untracked carve-out under the audio state dir.
    """
    p = audio_state_base() / "runtime"
    p.mkdir(parents=True, exist_ok=True)
    return p


def tts_output_dir() -> Path:
    """Return ``~/.scitex/audio/runtime/tts/`` for generated TTS files.

    This is the directory MCP handlers write timestamped ``tts_*.mp3``
    files into, and the directory ``list_audio_files`` /
    ``clear_audio_cache`` scan.
    """
    p = audio_runtime_dir() / "tts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def lock_dir() -> Path:
    """Return ``~/.scitex/audio/runtime/locks/`` for IPC lock files."""
    p = audio_runtime_dir() / "locks"
    p.mkdir(parents=True, exist_ok=True)
    return p


def audio_playback_lock_path() -> Path:
    """Path of the cross-process audio playback lock file."""
    return lock_dir() / "audio_playback.lock"


def cache_dir() -> Path:
    """Return ``~/.scitex/audio/runtime/cache/`` for transient caches."""
    p = audio_runtime_dir() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


# EOF
