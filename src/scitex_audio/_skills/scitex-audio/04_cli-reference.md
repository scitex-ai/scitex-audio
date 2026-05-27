---
description: |
  [TOPIC] scitex-audio CLI Reference
  [DETAILS] Top-level subcommands of the `scitex-audio` CLI — speak-text, backends, voices, check, relay, transcribe, mcp, skills.
tags: [scitex-audio-cli-reference]
---

# CLI Reference

`scitex-audio` is the entry point installed by `pip install scitex-audio`.

## Subcommands

| Command                          | Purpose                                       |
|----------------------------------|-----------------------------------------------|
| `scitex-audio speak-text "..."`  | Speak text (smart routing + backend fallback) |
| `scitex-audio list-backends`     | List available TTS backends                   |
| `scitex-audio check-backends`    | Diagnose audio output (WSL / local)           |
| `scitex-audio relay --port N`    | Start relay server (for headless / WSL hosts) |
| `scitex-audio stop-playback`     | Stop any currently playing speech             |
| `scitex-audio transcribe-audio FILE` | Speech-to-text via whisper.cpp            |
| `scitex-audio show-env-template` | Generate a template .src file for env config  |
| `scitex-audio list-python-apis`  | List all Python public APIs                   |
| `scitex-audio mcp start`         | Start MCP server (stdio) for AI agents        |
| `scitex-audio skills list`       | List embedded skill pages                     |
| `scitex-audio skills get <ID>`   | Retrieve one skill page                       |

Note: speak via `scitex-audio speak-text "..."` — the command is `speak-text`,
NOT `say`. Deprecated aliases (`speak`, `backends`, `check`, `transcribe`) still
work but print a redirect message — use the canonical names above.

## Examples

```bash
scitex-audio speak-text "Hello world"
scitex-audio speak-text "Use ElevenLabs" --backend elevenlabs --voice Rachel
scitex-audio list-backends
scitex-audio check-backends
scitex-audio relay --port 31293                   # on the laptop hosting speakers
scitex-audio transcribe-audio call.wav --model base
scitex-audio show-env-template -o ~/.scitex/audio/local.src
scitex-audio mcp start                            # speak MCP/stdio for an AI agent
```

See [11_cli-commands.md](11_cli-commands.md) for extended option-level details.
