#!/usr/bin/env python3
# Timestamp: "2025-12-27 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-code/src/scitex/audio/_mcp.tool_schemas.py
# ----------------------------------------

"""Tool schemas for the scitex-audio MCP server."""

from __future__ import annotations

import mcp.types as types

__all__ = ["get_tool_schemas"]


def get_tool_schemas() -> list[types.Tool]:
    """Return all tool schemas for the MCP server."""
    return [
        types.Tool(
            name="speak",
            description=(
                "Say text out loud — auto-selects and falls back across TTS backends "
                "(elevenlabs → luxtts → gtts → pyttsx3) and uses a sequential playback "
                "queue so concurrent agents don't overlap. Drop-in replacement for "
                "`pyttsx3.speak`, `gTTS(...).save + playback`, the `elevenlabs` Python "
                "SDK, and `say`/`espeak`/`spd-say` shelling. Use whenever the user asks "
                "to 'say X', 'speak this', 'voice notify me when done', 'read aloud', "
                "'announce that …', or needs spoken output. Set `save=True` to also "
                "keep the audio file, `wait=False` for fire-and-forget notifications."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech",
                    },
                    "backend": {
                        "type": "string",
                        "description": "TTS backend (auto-selects with fallback if not specified)",
                        "enum": ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice/language (gtts: 'en','fr'; elevenlabs: 'adam' [default], 'sarah','george','bella' — free-tier premade voices)",
                    },
                    "rate": {
                        "type": "integer",
                        "description": "Speech rate in words per minute (pyttsx3 only, default 150, faster=200+)",
                        "default": 150,
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speed multiplier for gtts (1.0=normal, 1.5=faster, 0.7=slower)",
                        "default": 1.5,
                    },
                    "play": {
                        "type": "boolean",
                        "description": "Play audio after generation",
                        "default": True,
                    },
                    "save": {
                        "type": "boolean",
                        "description": "Save audio to file",
                        "default": False,
                    },
                    "fallback": {
                        "type": "boolean",
                        "description": "Try next backend on failure",
                        "default": True,
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Optional identifier for the agent making the request",
                    },
                    "wait": {
                        "type": "boolean",
                        "description": "Wait for speech to complete before returning (default: True)",
                        "default": True,
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="generate_audio",
            description=(
                "Render text to an audio file on disk (no playback) via any TTS "
                "backend. Use whenever the user asks to 'save this as .mp3', "
                "'generate audio for this text', 'make a narration file', 'export "
                "spoken audio', or is building a dataset of synthesized speech. "
                "Returns the saved path, optionally base64-encoded bytes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to convert to speech",
                    },
                    "backend": {
                        "type": "string",
                        "description": "TTS backend",
                        "enum": ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
                        "default": "gtts",
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice/language",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output file path",
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "Return audio as base64",
                        "default": False,
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="list_backends",
            description=(
                "Inspect which TTS backends are installed and reachable — elevenlabs, "
                "luxtts, gtts, pyttsx3 — plus whether required env vars / API keys are "
                "set. Use when the user asks 'which TTS engines do I have?', 'is "
                "ElevenLabs configured?', 'what backends are available?', or is "
                "debugging why `speak` fell back to a lower-quality engine."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_voices",
            description=(
                "List the voices a given TTS backend offers — e.g. ElevenLabs premade "
                "voices (adam, sarah, george, bella), gTTS language codes (en, fr, ja, "
                "…), pyttsx3 system voices. Use when the user asks 'what voices can I "
                "use?', 'list ElevenLabs voices', 'which languages does gTTS support?', "
                "or before passing a `voice` argument to `speak`/`generate_audio`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "backend": {
                        "type": "string",
                        "description": "TTS backend",
                        "enum": ["elevenlabs", "luxtts", "gtts", "pyttsx3"],
                        "default": "gtts",
                    },
                },
            },
        ),
        types.Tool(
            name="play_audio",
            description=(
                "Play an existing audio file (WAV / MP3 / OGG / …) through the "
                "configured local or relay output. Drop-in replacement for `aplay`, "
                "`paplay`, `ffplay`, `afplay`, `playsound`, `pygame.mixer`. Use when "
                "the user asks to 'play this file', 'listen to /path/to/clip.mp3', "
                "'play back the recording', or 'route this audio to my laptop'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to audio file",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="list_audio_files",
            description=(
                "List previously generated audio files in the scitex-audio cache, "
                "newest first. Use when the user asks 'what audio did I generate?', "
                "'show recent TTS files', 'list the narrations', or before "
                "`clear_audio_cache` / replaying a recent clip via `play_audio`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum files to list",
                        "default": 20,
                    },
                },
            },
        ),
        types.Tool(
            name="clear_audio_cache",
            description=(
                "Delete generated TTS audio files from the cache — by default "
                "anything older than 24 h, or all of them with `max_age_hours=0`. "
                "Use when the user asks to 'clear audio cache', 'clean up TTS "
                "files', 'free disk from old narrations', or is tidying up after "
                "bulk generation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "max_age_hours": {
                        "type": "number",
                        "description": "Delete files older than N hours (0 = all)",
                        "default": 24,
                    },
                },
            },
        ),
        types.Tool(
            name="speech_queue_status",
            description=(
                "Inspect the sequential speech queue — what's currently playing, "
                "what's pending, whose agent_id is waiting. Use when the user asks "
                "'is anything queued?', 'why isn't my speak firing?', 'who's "
                "talking?', 'show the speech queue', or is debugging overlapped "
                "agent notifications."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="check_audio_status",
            description=(
                "Diagnose audio output — checks PulseAudio / ALSA / WSL audio "
                "bridge / relay server availability, reports which playback method "
                "will be used, and flags common WSL2 issues. Use when the user asks "
                "'is audio working?', 'why can't I hear TTS?', 'debug WSL audio', "
                "'check relay connection', or before a long session that depends "
                "on reliable audio."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="announce_context",
            description=(
                "Speak out the current working directory and git branch — useful "
                "startup ping so the user hears 'scitex-audio, branch develop' "
                "when opening a new terminal or session. Use when the user asks "
                "to 'announce context', 'tell me where I am', 'say the current "
                "branch', or wants an audible orientation at session start."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include_full_path": {
                        "type": "boolean",
                        "description": "Include full path or just directory name",
                        "default": False,
                    },
                },
            },
        ),
    ]


# EOF
