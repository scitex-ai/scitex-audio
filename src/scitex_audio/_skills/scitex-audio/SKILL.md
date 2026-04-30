---
description: Unified text-to-speech (ElevenLabs / LuxTTS / gTTS / pyttsx3 with automatic fallback) AND local speech-to-text (whisper.cpp — tiny / base / small / medium / large-v3-turbo models). Smart local/relay routing so headless servers or WSL machines play audio on your laptop via a lightweight relay, SSH-tunnelable. Sequential playback queue prevents audio overlap when multiple agents speak concurrently. Drop-in replacement for raw `pyttsx3`, `gTTS`, `elevenlabs` SDK, `sounddevice` playback, `ffplay`/`aplay`/`paplay` shelling, and `openai-whisper` / `faster-whisper` Python libs. Use whenever the user asks to "say this", "speak", "play this text aloud", "voice notification", "read this out loud", "TTS this", "generate an audio file of …", "transcribe this audio", "speech to text", "whisper this .wav / .mp3", "convert audio to text", "play audio on my laptop from the server", "check WSL audio", "announce the branch / directory", or needs voice I/O in any form.
allowed-tools: mcp__scitex__audio_*
primary_interface: mcp
interfaces:
  python: 2
  cli: 1
  mcp: 3
  skills: 2
  hook: 0
  http: 0
name: scitex-audio
tags: [scitex-audio, scitex-package]
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

### Core
* [01_quick-start](01_quick-start.md) — Basic usage, first call, return values
* [02_available-backends](02_available-backends.md) — All TTS backends, capabilities, install commands
* [03_smart-routing](03_smart-routing.md) — Auto/local/remote modes, relay server, SSH tunneling

### Workflows
* [10_common-workflows](10_common-workflows.md) — Notification patterns, multi-backend, save audio
* [11_cli-commands](11_cli-commands.md) — Complete CLI reference
* [12_mcp-tools-for-ai-agents](12_mcp-tools-for-ai-agents.md) — MCP tools and installation

## MCP Tools

| Tool | Purpose |
|------|---------|
| `audio_speak` / `speak` | Speak text with smart routing + backend fallback |
| `generate_audio` | Render speech to file (no playback) |
| `list_backends` / `list_voices` | Inspect TTS backends and voices |
| `play_audio` | Play an existing audio file |
| `list_audio_files` / `clear_audio_cache` | Manage generated audio |
| `speech_queue_status` | Inspect queue of pending utterances |
| `check_audio_status` | Diagnose WSL / local audio connectivity |
| `announce_context` | Say current working dir + git branch |
| `audio_transcribe` | Speech-to-text via whisper.cpp (any audio format) |
| `list_whisper_models` | Show installed whisper models + CLI status |

## CLI

```bash
scitex-audio speak "Hello world"          # Basic speech
scitex-audio backends                     # List available backends
scitex-audio check                        # Check audio status (WSL)
scitex-audio relay --port 31293          # Start relay server
scitex-audio mcp start                   # Start MCP server (stdio)
scitex-audio skills list                 # List skill pages
```


## Environment

- [20_env-vars.md](20_env-vars.md) — SCITEX_* env vars read by scitex-audio at runtime
