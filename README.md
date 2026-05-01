<!-- ---
!-- Timestamp: 2026-03-14 07:25:51
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/scitex-audio/README.md
!-- --- -->

# SciTeX Audio (<code>scitex-audio</code>)

<!-- scitex-badges:start -->
[![PyPI](https://img.shields.io/pypi/v/scitex-audio.svg)](https://pypi.org/project/scitex-audio/)
[![Python](https://img.shields.io/pypi/pyversions/scitex-audio.svg)](https://pypi.org/project/scitex-audio/)
[![Tests](https://github.com/ywatanabe1989/scitex-audio/actions/workflows/test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-audio/actions/workflows/test.yml)
[![Install Test](https://github.com/ywatanabe1989/scitex-audio/actions/workflows/install-test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-audio/actions/workflows/install-test.yml)
[![Coverage](https://codecov.io/gh/ywatanabe1989/scitex-audio/graph/badge.svg)](https://codecov.io/gh/ywatanabe1989/scitex-audio)
[![Docs](https://readthedocs.org/projects/scitex-audio/badge/?version=latest)](https://scitex-audio.readthedocs.io/en/latest/)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- scitex-badges:end -->

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center">
  <a href="https://scitex-audio.readthedocs.io/">Full Documentation</a> · <code>pip install scitex-audio</code>
</p>

---

## Problem and Solution

| # | Problem | Solution |
|---|---------|----------|
| 1 | **TTS libraries balkanized** -- ElevenLabs REST + gTTS HTTP + pyttsx3 native each have different APIs, failure modes, voice formats | **`stx.audio.speak(text)`** -- one call; automatic fallback ElevenLabs → LuxTTS → gTTS → pyttsx3 when upstream fails or API key is missing |
| 2 | **Offline TTS sounds robotic** -- espeak is a pi-era stopgap | **LuxTTS** -- offline 48 kHz voice-cloning on CPU; near-realtime after first-load warmup |
| 3 | **Scripts can't alert users from a headless session** -- `print` gets lost in logs | **MCP tool `audio_speak`** -- agents and long-running scripts report status audibly to the operator, with desktop notification fallback |

## TTS Backends

| Backend | Quality | Cost | Internet | Offline | Default Speed |
|---------|---------|------|----------|---------|---------------|
| **ElevenLabs** | High | Paid | Required | No | 1.2x |
| **LuxTTS** | High | Free | First download | Yes | 2.0x |
| **Google TTS** | Good | Free | Required | No | 1.5x |
| **System TTS** | Basic | Free | No | Yes | 150 wpm |

<p align="center"><sub><b>Table 1.</b> Supported TTS backends. The fallback order (elevenlabs → luxtts → gtts → pyttsx3) ensures the best available quality is always used.</sub></p>

## Installation

Requires Python >= 3.10.

```bash
pip install scitex-audio
```

Install with specific backends:

```bash
pip install scitex-audio[gtts]         # Google TTS
pip install scitex-audio[pyttsx3]      # System TTS (+ apt install espeak-ng)
pip install scitex-audio[elevenlabs]   # ElevenLabs
pip install scitex-audio[luxtts]       # LuxTTS (voice cloning, offline)
pip install scitex-audio[all]          # Everything
```

## Quick Start

```python
from scitex_audio import speak, available_backends

# Check what's available
print(available_backends())  # e.g., ['gtts', 'pyttsx3']

# Speak with auto-selected backend
speak("Hello from SciTeX Audio!")

# Choose a specific backend
speak("Bonjour", backend="gtts", voice="fr")

# Save without playing
speak("Save this", output_path="output.mp3", play=False)
```

## Four Interfaces

<details open>
<summary><strong>Python API</strong></summary>

<br>

```python
import scitex_audio

scitex_audio.speak("Hello!")                         # auto backend
scitex_audio.speak("Fast", backend="gtts", speed=1.5)
scitex_audio.available_backends()                    # list backends
scitex_audio.check_wsl_audio()                       # WSL audio status
scitex_audio.generate_bytes("As bytes")              # raw MP3 bytes
scitex_audio.stop_speech()                           # kill playback

tts = scitex_audio.get_tts("gtts")                   # get engine
tts.speak("With engine", voice="fr")
```

> **[Full API reference](https://scitex-audio.readthedocs.io/en/latest/api/scitex_audio.html)**

</details>

<details>
<summary><strong>CLI Commands</strong></summary>

<br>

```bash
scitex-audio --help-recursive             # Show all commands
scitex-audio speak "Hello world"          # Speak text
scitex-audio speak "Bonjour" -b gtts -v fr
scitex-audio backends                     # List backends
scitex-audio check                        # Audio status (WSL)
scitex-audio stop                         # Stop playback
scitex-audio relay --port 31293           # Start relay server
scitex-audio list-python-apis             # List Python API tree
scitex-audio mcp list-tools               # List MCP tools
```

> **[Full CLI reference](https://scitex-audio.readthedocs.io/en/latest/quickstart.html)**

</details>

<details>
<summary><strong>MCP Server — for AI Agents</strong></summary>

<br>

AI agents can speak through the MCP protocol for notifications and accessibility. The agent generates text, the MCP server synthesizes speech on the host machine, and audio plays through the user's local speakers — even when the agent runs on a remote server (via the [relay](#remote-audio-relay) on port `31293`).

| Tool | Description |
|------|-------------|
| `audio_speak` | Convert text to speech with backend fallback |
| `list_backends` | List available TTS backends and status |
| `check_audio_status` | Check WSL audio connectivity |
| `announce_context` | Announce current directory and git branch |

<sub><b>Table 2.</b> Four MCP tools available for AI-assisted audio. All tools accept JSON parameters and return JSON results.</sub>

#### Claude Code Setup

Add `.mcp.json` to your project root. Use `SCITEX_AUDIO_ENV_SRC` to load all configuration from a `.src` file — this keeps `.mcp.json` static across environments:

```json
{
  "mcpServers": {
    "scitex-audio": {
      "command": "scitex-audio",
      "args": ["mcp", "start"],
      "env": {
        "SCITEX_AUDIO_ENV_SRC": "${SCITEX_AUDIO_ENV_SRC}"
      }
    }
  }
}
```

Then switch environments via your shell profile:

```bash
# Local machine (has speakers)
export SCITEX_AUDIO_ENV_SRC=~/.scitex/audio/local.src

# Remote server (no speakers, uses relay)
export SCITEX_AUDIO_ENV_SRC=~/.scitex/audio/remote.src
```

Generate a template `.src` file:

```bash
scitex-audio env-template -o ~/.scitex/audio/local.src
```

Example `local.src`:

```bash
export SCITEX_AUDIO_MODE=local
export SCITEX_AUDIO_RELAY_PORT=31293
export SCITEX_AUDIO_ELEVENLABS_API_KEY="your-key-here"
```

Example `remote.src`:

```bash
export SCITEX_AUDIO_MODE=remote
export SCITEX_AUDIO_RELAY_PORT=31293
export SCITEX_AUDIO_ELEVENLABS_API_KEY="your-key-here"
```

Or install globally:

```bash
scitex-audio mcp install
```

> **[Full MCP specification](https://scitex-audio.readthedocs.io/en/latest/api/scitex_audio._mcp.html)**

</details>

<details>
<summary><strong>Skills</strong></summary>

<br>

Skills provide workflow-oriented guides that AI agents query to discover capabilities and usage patterns.

```bash
scitex-audio skills list              # List available skill pages
scitex-audio skills get SKILL         # Show main skill page
scitex-dev skills export --package scitex-audio  # Export to Claude Code
```

| Skill | Content |
|-------|---------|
| `quick-start` | Basic usage, first call, return values |
| `available-backends` | All TTS backends, capabilities, install commands |
| `smart-routing` | Auto/local/remote modes, relay server, SSH tunneling |
| `cli-commands` | Complete CLI reference |
| `mcp-tools-for-ai-agents` | MCP tools and installation |
| `common-workflows` | Notification patterns, multi-backend, save audio |

</details>

<details>
<summary><strong>Remote Audio Relay</strong></summary>

<br>

When agents run on remote servers (NAS, cloud, HPC), they have no speakers. The **relay server** solves this: the local machine (with speakers) runs a lightweight HTTP server, and the remote agent sends speech requests over an SSH tunnel.

### Architecture

```
Remote Server (NAS/Cloud)          Local Machine (has speakers)
┌─────────────────────┐            ┌──────────────────────┐
│ AI Agent            │            │ Relay Server         │
│   speak("Hello")    │            │   scitex-audio relay │
│     ↓               │            │     ↓                │
│ POST /speak ────────┼── SSH ─────┼→ TTS engine          │
│   (port 31293)      │  tunnel    │     ↓                │
│                     │            │   🔊 Speakers        │
└─────────────────────┘            └──────────────────────┘
```

### Setup

**Step 1: Start relay on local machine (has speakers)**

```bash
scitex-audio relay --port 31293
```

**Step 2: SSH tunnel from local to remote**

Add to your `~/.ssh/config`:

```ssh-config
Host my-server
  HostName 192.168.0.69
  User myuser
  RemoteForward 31293 127.0.0.1:31293   # Audio relay
```

Then connect: `ssh my-server`. The tunnel maps remote port 31293 back to your local relay.

**Step 3: Configure remote environment**

On the remote server, set:

```bash
export SCITEX_AUDIO_MODE=remote
export SCITEX_AUDIO_RELAY_PORT=31293
# URL is auto-detected from the tunnel (localhost:31293)
```

Now `speak("Hello")` on the remote server plays audio on your local speakers.

### Relay Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/speak` | POST | Play TTS (`{"text": "...", "backend": "gtts"}`) |
| `/health` | GET | Health check (returns `{"status": "ok"}`) |
| `/list_backends` | GET | List available backends |

### Auto-Start Relay (Shell Profile)

Add to your shell profile (e.g., `~/.bashrc`) on the **local machine** (the one with speakers):

```bash
export SCITEX_AUDIO_RELAY_PORT=31293
export SCITEX_AUDIO_MODE=local

_audio_health_ok() {
    local port="${SCITEX_AUDIO_RELAY_PORT:-31293}"
    curl -sf --connect-timeout 2 "http://localhost:$port/health" >/dev/null 2>&1
}

_start_audio_relay() {
    local port="${SCITEX_AUDIO_RELAY_PORT:-31293}"

    # Already healthy -> skip
    _audio_health_ok && return

    # Start relay in background
    scitex-audio relay --port "$port" --force &>/dev/null &
    disown
}

_start_audio_relay
```

On the **remote server** (NAS, cloud, HPC), add to the shell profile:

```bash
export SCITEX_AUDIO_RELAY_PORT=31293
export SCITEX_AUDIO_MODE=remote
# Relay URL is auto-detected from the SSH RemoteForward tunnel
```

With this setup, every SSH session automatically has audio routed back to your speakers. AI agents (Claude Code, etc.) running on the remote server call `speak()` and the audio plays locally.

</details>

<details>
<summary><strong>Environment Variables</strong></summary>

<br>

| Variable | Default | Description |
|----------|---------|-------------|
| `SCITEX_AUDIO_MODE` | `auto` | Audio mode: `local`, `remote`, or `auto` |
| `SCITEX_AUDIO_RELAY_URL` | *(auto)* | Full relay URL (e.g., `http://localhost:31293`) |
| `SCITEX_AUDIO_RELAY_HOST` | *(none)* | Relay host (combined with port to build URL) |
| `SCITEX_AUDIO_RELAY_PORT` | `31293` | Relay server port |
| `SCITEX_AUDIO_HOST` | `0.0.0.0` | Relay server bind host |
| `SCITEX_AUDIO_ELEVENLABS_API_KEY` | *(none)* | ElevenLabs API key |
| `SCITEX_DIR` | `~/.scitex` | Base directory for audio cache files |
| `SCITEX_CLOUD` | *(none)* | Set to `true` for browser relay mode (OSC escape) |

<p align="center"><sub><b>Table 3.</b> Environment variables. Port 31293 encodes "sa-i-te-ku-su" (サイテクス) in Japanese phone keypad mapping.</sub></p>

### Mode Resolution

- **`auto`** (default): Checks local audio availability. If suspended/unavailable and relay URL detected, routes to relay. Otherwise uses local.
- **`local`**: Always use local TTS engine and speakers.
- **`remote`**: Always send speech to relay server. Fails if relay unreachable.

</details>

## Part of SciTeX

`scitex-audio` is part of [**SciTeX**](https://scitex.ai). Install via
the umbrella with `pip install scitex[audio]` to use as
`scitex.audio` (Python) or `scitex audio ...` (CLI).

The SciTeX system follows the Four Freedoms for Research below, inspired by [the Free Software Definition](https://www.gnu.org/philosophy/free-sw.en.html):

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

## Acknowledgements

- [LuxTTS](https://github.com/ysharma3501/LuxTTS) — open-source, offline TTS engine with voice cloning support

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>

<!-- EOF -->
