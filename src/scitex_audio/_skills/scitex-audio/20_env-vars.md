---
description: |
  [TOPIC] Env Vars
  [DETAILS] Environment variables read by scitex-audio at import / runtime. Follow SCITEX_<MODULE>_* convention — see general/10_arch-environment-variables.md.
tags: [scitex-audio-env-vars]
---

# scitex-audio — Environment Variables

## Core

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_AUDIO_MODE` | Routing mode (`local`, `remote`, `auto`). | `auto` | string |
| `SCITEX_AUDIO_HOST` | Bind host for relay/MCP server. | `0.0.0.0` | string |
| `SCITEX_AUDIO_PORT` | Port for relay/MCP server. | `31293` | int |
| `SCITEX_AUDIO_ENV_SRC` | Env-file sourced at CLI start. | unset | path |

## Relay (remote playback)

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_AUDIO_RELAY_URL` | Full relay URL (overrides host/port). | unset | URL |
| `SCITEX_AUDIO_RELAY_HOST` | Relay hostname. | unset | string |
| `SCITEX_AUDIO_RELAY_PORT` | Relay port. | `31293` | int |

## Backends

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_AUDIO_ELEVENLABS_API_KEY` | ElevenLabs TTS API key. | `—` | string (optional) |
| `SCITEX_AUDIO_LUXTTS_REFERENCE` | Reference audio path for LuxTTS voice cloning. | unset | path |
| `SCITEX_AUDIO_LUXTTS_TRIM_START` | Seconds to trim from clone reference start. | `0.0` | float |
| `SCITEX_AUDIO_WHISPER_CLI` | Path to a `whisper` CLI binary (STT). | auto | path |
| `SCITEX_AUDIO_WHISPER_MODEL` | Whisper model size (`tiny`/`base`/`small`/...). | `tiny` | string |

## Cross-package (ecosystem-wide)

| Variable | Owner | Purpose |
|---|---|---|
| `SCITEX_DIR` | ecosystem | Base SciTeX data dir. |
| `SCITEX_BASE_DIR` | ecosystem | Legacy alias for `SCITEX_DIR`. |
| `SCITEX_CLOUD` | scitex-cloud | Cloud presence flag. |

## Feature flags

None module-private (no opt-in/opt-out booleans in current source).

## Audit

```bash
grep -rhoE 'SCITEX_[A-Z0-9_]+' $HOME/proj/scitex-audio/src/ | sort -u
```
