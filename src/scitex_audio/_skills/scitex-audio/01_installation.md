---
description: |
  [TOPIC] Installation
  [DETAILS] pip install scitex-audio. Python core with explicit optional TTS backends. Optional ElevenLabs/LuxTTS/whisper.cpp backends activated if their deps/binaries are present.
tags: [scitex-audio-installation]
---

# Installation

## Standard

```bash
pip install scitex-audio
```

The base package provides the core interfaces. Install the optional TTS
backends you use, for example `pip install 'scitex-audio[gtts,pyttsx3]'`.
Speech-to-text also needs the external binary and model described below.

## Optional backends

| Backend       | Install                                          | Notes                       |
|---------------|--------------------------------------------------|-----------------------------|
| ElevenLabs    | `pip install scitex-audio[elevenlabs]` + `ELEVENLABS_API_KEY` | Premium cloud TTS |
| LuxTTS        | `pip install scitex-audio[luxtts]`               | Local high-quality TTS      |
| whisper.cpp   | install `whisper-cli` binary + a model           | Local STT (auto-detected)   |

## Local speech-to-text setup (whisper.cpp)

`pip install scitex-audio` and the `[all]` Python extra do not install
`whisper-cli` or GGML model weights. The existing `dev system-deps` installer
provides audio OS dependencies, not whisper.cpp or its models.

For a POSIX shell, start with Git, CMake and a C++ toolchain installed. Follow
the [upstream whisper.cpp quick start](https://github.com/ggml-org/whisper.cpp#quick-start)
for platform-specific prerequisites. A CPU build and explicit model paths are:

```bash
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build -DGGML_CUDA=OFF
cmake --build build --config Release -j 2
bash models/download-ggml-model.sh base
export SCITEX_AUDIO_WHISPER_CLI="$PWD/build/bin/whisper-cli"
export SCITEX_AUDIO_WHISPER_MODEL="$PWD/models/ggml-base.bin"
```

Both environment variables are **file paths**. The model override takes
precedence over `--model`, so keep the selected name and file consistent.
The binary can instead be on PATH. An explicit override must name an existing
file, and the CLI file must be executable; a bad override is reported missing
rather than silently selecting another binary or model. Do not assume an
Emacs cache exists.

```bash
"$SCITEX_AUDIO_WHISPER_CLI" --help
scitex-audio transcribe-audio /path/to/recording.wav --model base --language ja
scitex-audio transcribe-audio /path/to/recording.wav --model base --language auto --json
```

The CLI defaults to Japanese (`ja`) and the `tiny` model. `--language auto`
explicitly requests detection. The examples choose `base` to match the
configured file; they are not a Japanese quality benchmark. For non-WAV
input, also install ffmpeg. Missing prerequisites and failed transcription
return a failure payload and nonzero CLI status, including with `--json`.

No `--device`, `--host`, URL/channel input or resumable batch interface is
provided by this command. Do not infer GPU support from a local playback
relay; those are separate capabilities.

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
