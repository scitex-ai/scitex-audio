---
description: Text-to-speech with multiple backends (ElevenLabs, LuxTTS, gTTS, pyttsx3), smart local/relay routing, and MCP tools. Use when generating speech, playing audio notifications, or routing audio between machines.
allowed-tools: mcp__scitex__audio_*
---

# scitex-audio

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
| `audio_speak` | Speak text with smart routing and backend selection |

## CLI

```bash
scitex-audio speak "Hello world"          # Basic speech
scitex-audio backends                     # List available backends
scitex-audio check                        # Check audio status (WSL)
scitex-audio relay --port 31293          # Start relay server
scitex-audio mcp start                   # Start MCP server (stdio)
scitex-audio skills list                 # List skill pages
```
