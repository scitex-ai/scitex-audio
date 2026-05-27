---
name: scitex-audio
description: |
  [WHAT] Unified text-to-speech (ElevenLabs / LuxTTS / gTTS / pyttsx3 with automatic fallback) AND local speech-to-text (whisper.cpp — tiny / base / small / medium / large-v3-turbo models). Smart local/relay routing so headless servers or WSL machines play audio on your laptop via a lightweight relay, SSH-tunnelable. Sequential playback queue prevents audio overlap when multiple agents speak concurrently…
  [WHEN] Use whenever the user asks to "say this", "speak", "play this text aloud", "voice notification", "read this out loud", "TTS this", "generate an audio file of …", "transcribe this audio", "speech to text", "whisper this .
  [HOW] wav / .mp3", "convert audio to text", "play audio on my laptop from the server", "check WSL audio", "announce the branch / directory", or needs voice I/O in any form.
tags: [scitex-audio]
allowed-tools: mcp__scitex__audio_*
primary_interface: mcp
interfaces:
  python: 2
  cli: 1
  mcp: 3
  skills: 2
  http: 0
---

# scitex-audio

> **Interfaces:** Python ⭐⭐ · CLI ⭐ · MCP ⭐⭐⭐ (primary) · Skills ⭐⭐ · Hook — · HTTP —

Text-to-speech with multiple backends and smart local/relay routing.

## Installation & import (two equivalent paths)

The same module is reachable via two install paths. Both forms work at
runtime; which one a user has depends on their install choice.

```python
# Standalone — pip install scitex-audio
import scitex_audio
scitex_audio.speak(...)

# Umbrella — pip install scitex
import scitex.audio
scitex.audio.speak(...)
```

`pip install scitex-audio` alone does NOT expose the `scitex` namespace;
`import scitex.audio` raises `ModuleNotFoundError`. To use the
`scitex.audio` form, also `pip install scitex`.

See [../../general/02_interface-python-api.md] for the ecosystem-wide
rule and empirical verification table.

## Sub-skills

* Core: [01_installation](01_installation.md), [02_quick-start](02_quick-start.md), [03_python-api](03_python-api.md), [04_cli-reference](04_cli-reference.md)
* Workflows: [10_common-workflows](10_common-workflows.md), [11_cli-commands](11_cli-commands.md), [12_mcp-tools-for-ai-agents](12_mcp-tools-for-ai-agents.md)
* Backends: [14_available-backends](14_available-backends.md), [15_smart-routing](15_smart-routing.md)

## MCP Tools

| Tool | Purpose |
|------|---------|
| `audio_speak` | Speak text with smart routing + backend fallback |
| `audio_generate_bytes` | Render speech to file (no playback) |
| `audio_available_backends` | Inspect TTS backends |
| `audio_check_wsl_audio` | Diagnose WSL audio connectivity |
| `audio_check_local_audio_available` | Check PulseAudio sink state |
| `audio_stop_speech` | Stop any currently playing speech |
| `audio_announce_context` | Say current working dir + git branch |
| `audio_transcribe` | Speech-to-text via whisper.cpp (any audio format) |
| `audio_available_models` | Show installed whisper models + CLI status |
| `audio_skills_list` / `audio_skills_get` | Introspect bundled skill pages |

## CLI

```bash
scitex-audio speak-text "Hello world"     # Basic speech
scitex-audio list-backends                # List available backends
scitex-audio check-backends               # Check audio status (WSL)
scitex-audio relay --port 31293           # Start relay server
scitex-audio mcp start                    # Start MCP server (stdio)
scitex-audio transcribe-audio file.wav    # Speech-to-text via whisper.cpp
scitex-audio skills list                  # List skill pages
```


## Environment

- [20_env-vars.md](20_env-vars.md) — SCITEX_* env vars read by scitex-audio at runtime
