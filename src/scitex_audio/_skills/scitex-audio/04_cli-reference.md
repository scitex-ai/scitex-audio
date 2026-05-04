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
| `scitex-audio backends`          | List available TTS backends                   |
| `scitex-audio voices [BACKEND]`  | List voices for a backend                     |
| `scitex-audio check`             | Diagnose audio output (WSL / local)           |
| `scitex-audio relay --port N`    | Start relay server (for headless / WSL hosts) |
| `scitex-audio transcribe FILE`   | Speech-to-text via whisper.cpp                |
| `scitex-audio mcp start`         | Start MCP server (stdio) for AI agents        |
| `scitex-audio skills list`       | List embedded skill pages                     |
| `scitex-audio skills get <ID>`   | Retrieve one skill page                       |

Note: speak via `scitex-audio speak-text "..."` — the command is `speak-text`,
NOT `say`.

## Examples

```bash
scitex-audio speak-text "Hello world"
scitex-audio speak-text "Use ElevenLabs" --backend elevenlabs --voice Rachel
scitex-audio backends
scitex-audio check
scitex-audio relay --port 31293                   # on the laptop hosting speakers
scitex-audio transcribe call.wav --model base
scitex-audio mcp start                            # speak MCP/stdio for an AI agent
```

See [11_cli-commands.md](11_cli-commands.md) for extended option-level details.
