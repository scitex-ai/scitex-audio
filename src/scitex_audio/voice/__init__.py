#!/usr/bin/env python3
# Timestamp: "2026-08-16 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/voice/__init__.py

"""SciTeX Voice V1 — speaker-verified dictation (audio side).

Only the enrolled operator's speech reaches ASR; neighbours and BGM are
discarded. This subpackage owns WHAT WE DO WITH AUDIO; the embedding +
similarity model lives in scitex-ml. Card:
scitex-voice-speaker-verified-dictation-v1-20260816.

V1 pipeline (five parts, no sixth):
    mic 16 kHz mono  ->  VAD  ->  speaker-verify gate  ->  whisper.cpp
    (Windows client)     vad/     speaker/verify/          asr/

Submodules:
    io/       mono-16k read/write + framing (this PR)
    vad/      speech-vs-silence segmentation (this PR)
    asr/      segment-level whisper.cpp adapter over scitex_audio._stt (this PR)
    speaker/  enroll / verify / extract   (later PRs; extract is a V2 stub)
    pipeline/ mic -> gate -> ASR orchestration + WS endpoint (later PR)

Import-safety: submodules pull heavy deps (soundfile/torch) lazily, so
``import scitex_audio.voice`` never requires them.
"""

from __future__ import annotations

from . import asr, io, vad

__all__ = ["io", "vad", "asr"]
