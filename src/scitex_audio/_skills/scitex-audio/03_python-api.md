---
description: |
  [TOPIC] Python API
  [DETAILS] Public callables — speak, generate_bytes, available_backends, get_tts, transcribe, check_wsl_audio, stop_speech.
tags: [scitex-audio-python-api]
---

# Python API

## Imports

```python
import scitex_audio
# or via umbrella:
import scitex.audio
```

## TTS (text-to-speech)

```python
from scitex_audio import speak, generate_bytes, available_backends, get_tts

speak("Hello world")                              # smart routing + fallback
speak("Hi", backend="gtts")                       # force a backend

mp3 = generate_bytes("Render to bytes")           # no playback
backends = available_backends()                   # ['gtts', 'pyttsx3', ...]
tts = get_tts("elevenlabs", voice="Rachel")       # explicit handle
```

## STT (speech-to-text, whisper.cpp)

```python
from scitex_audio import transcribe, available_models, find_whisper_cli

text = transcribe("recording.wav", model="base")
models = available_models()                       # installed whisper models
binary = find_whisper_cli()                       # locate whisper-cli binary
```

## Diagnostics & control

```python
from scitex_audio import (
    check_wsl_audio, check_local_audio_available, stop_speech,
)

check_wsl_audio()                                 # dict of routing diagnostics
check_local_audio_available()
stop_speech()                                     # interrupt current playback
```

## Queue + concurrency

`speak()` uses an internal sequential queue so concurrent agents don't
overlap. See [12_mcp-tools-for-ai-agents.md](12_mcp-tools-for-ai-agents.md)
for the equivalent MCP tools and queue inspection.

## Backends and routing

See [14_available-backends.md](14_available-backends.md) for backend details
and [15_smart-routing.md](15_smart-routing.md) for the WSL/relay model.
