---
description: |
  [TOPIC] Installation
  [DETAILS] pip install scitex-audio. Pure-Python core; gTTS works out of the box. Optional ElevenLabs/LuxTTS/whisper.cpp backends activated if their deps/binaries are present.
tags: [scitex-audio-installation]
---

# Installation

## Standard

```bash
pip install scitex-audio
```

Out of the box: `gTTS` (network) + `pyttsx3` (offline system voice).

## Optional backends

| Backend       | Install                                          | Notes                       |
|---------------|--------------------------------------------------|-----------------------------|
| ElevenLabs    | `pip install scitex-audio[elevenlabs]` + `ELEVENLABS_API_KEY` | Premium cloud TTS |
| LuxTTS        | `pip install scitex-audio[luxtts]`               | Local high-quality TTS      |
| whisper.cpp   | install `whisper-cli` binary + a model           | Local STT (auto-detected)   |

## Linux audio playback

`scitex-audio` plays via `aplay` / `paplay` / `mpg123` — install one if your
distro lacks them. On WSL, run a relay on the Windows host (see
[15_smart-routing.md](15_smart-routing.md)).

## Verify

```bash
scitex-audio backends                       # list available TTS backends
scitex-audio check                          # diagnose audio output
scitex-audio speak-text "hello world"
python -c "import scitex_audio; print(scitex_audio.__version__)"
```

## Editable install (development)

```bash
git clone https://github.com/ywatanabe1989/scitex-audio
cd scitex-audio
pip install -e .
```
