#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: src/scitex_audio/_system_deps.py
"""System (apt) dependency declarations for scitex-audio.

scitex-audio is the single source of truth for the OS-level packages its
audio/video pipeline needs. They are published under the
``scitex_dev.system_deps`` entry-point group so scitex-dev's aggregator
(``scitex-dev ecosystem system-deps``) federates them into ONE apt set at
container-build time, instead of hardcoding/duplicating apt lists in
container definitions.

apt requires root, so installation happens at IMAGE-BUILD time (a container
``%post`` / Dockerfile), never at agent boot (agents run rootless
``--userns``). Declarations live here; install is build-time.
"""

from __future__ import annotations

import dataclasses

#: The declaring package name recorded on every SystemDepSpec.
PROVIDER = "scitex-audio"


@dataclasses.dataclass(frozen=True)
class _Dep:
    """A keystone-independent apt declaration (so the CLI works even when an
    older scitex-dev without ``system_deps`` is installed)."""

    package: str
    purpose: str
    apt_repo: str | None = None


_APT_DEPS = [
    _Dep("ffmpeg", "audio/video decode + encode for playback and speak (pydub)"),
    _Dep(
        "portaudio19-dev",
        "PortAudio dev headers for sounddevice / pyaudio capture + playback",
    ),
]


def declarations() -> list[_Dep]:
    """Return scitex-audio's raw apt declarations.

    Used by the leaf CLI so ``scitex-audio dev system-deps`` renders without
    requiring the scitex-dev keystone to be importable.
    """
    return list(_APT_DEPS)


def provide():
    """Entry point for the ``scitex_dev.system_deps`` group.

    Maps this package's declarations onto scitex-dev's ``SystemDepSpec`` so the
    ecosystem aggregator can federate them. Imported lazily: scitex-dev is a
    hard dependency, but only the aggregator (which runs with a keystone-capable
    scitex-dev) needs this call to succeed.
    """
    from scitex_dev.system_deps import SystemDepSpec

    return [
        SystemDepSpec(
            package=dep.package,
            purpose=dep.purpose,
            provider=PROVIDER,
            apt_repo=dep.apt_repo,
        )
        for dep in _APT_DEPS
    ]


# EOF
