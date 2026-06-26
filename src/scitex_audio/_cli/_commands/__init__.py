#!/usr/bin/env python3
"""Subcommand modules for the ``scitex-audio`` CLI.

Each module exposes ``register(group)`` that attaches its commands to the
passed Click group. ``_cli/_main.py`` defines the ``audio`` group and calls
every ``register`` in turn, keeping the orchestrator thin.
"""

from ._backends import register as register_backends
from ._env import register as register_env
from ._playback import register as register_playback
from ._speak import register as register_speak
from ._stt import register as register_stt
from ._system_deps import register as register_system_deps

__all__ = [
    "register_backends",
    "register_env",
    "register_playback",
    "register_speak",
    "register_stt",
    "register_system_deps",
]

# EOF
