Quick Start
===========

Installation
------------

Requires Python >= 3.10.

.. code-block:: bash

   pip install scitex-audio

Install with specific backends:

.. code-block:: bash

   pip install scitex-audio[gtts]         # Google TTS
   pip install scitex-audio[pyttsx3]      # System TTS (+ apt install espeak-ng)
   pip install scitex-audio[elevenlabs]   # ElevenLabs (paid, high quality)
   pip install scitex-audio[luxtts]       # LuxTTS (offline, voice cloning)
   pip install scitex-audio[all]          # Everything

Python API
----------

.. code-block:: python

   from scitex_audio import speak, available_backends, get_tts

   # Check available backends
   print(available_backends())  # ['gtts', 'pyttsx3']

   # Speak with auto-selected best backend
   speak("Hello from SciTeX Audio!")

   # Choose backend and voice
   speak("Bonjour", backend="gtts", voice="fr")

   # Control speed
   speak("Fast speech", backend="gtts", speed=1.5)
   speak("LuxTTS speech", backend="luxtts", speed=2.0)

   # Save without playing
   speak("Save this", output_path="output.mp3", play=False)

   # Get raw audio bytes
   from scitex_audio import generate_bytes
   audio_bytes = generate_bytes("As bytes")

   # Use engine directly
   tts = get_tts("gtts")
   tts.speak("With engine", voice="fr")

CLI
---

.. code-block:: bash

   # Basic speech
   scitex-audio speak "Hello world"
   scitex-audio speak "Bonjour" --backend gtts --voice fr

   # Backend management
   scitex-audio backends              # List available backends
   scitex-audio check                 # Audio status (WSL detection)
   scitex-audio stop                  # Stop current playback

   # Relay server (for remote audio)
   scitex-audio relay --port 31293

   # MCP server (for AI agents)
   scitex-audio mcp start
   scitex-audio mcp list-tools

   # Introspection
   scitex-audio list-python-apis      # Full Python API tree
   scitex-audio --help-recursive      # All commands and options

MCP Server
----------

AI agents can use the MCP protocol for text-to-speech:

.. code-block:: bash

   # Start MCP server (stdio transport, for Claude/other agents)
   scitex-audio mcp start

   # HTTP transport (for remote agents)
   scitex-audio mcp start -t http --port 31293

Available MCP tools:

- ``audio_speak`` — Convert text to speech with backend fallback
- ``audio_generate_bytes`` — Generate TTS audio to file without playing
- ``audio_available_backends`` — List available TTS backends and status
- ``audio_check_local_audio_available`` — Check PulseAudio sink state
- ``audio_stop_speech`` — Stop any currently playing speech
- ``audio_announce_context`` — Announce current directory and git branch
- ``audio_transcribe`` — Speech-to-text via whisper.cpp
- ``audio_available_models`` — Show installed whisper models + CLI status

Claude Code Setup
~~~~~~~~~~~~~~~~~

Add ``.mcp.json`` to your project root. Use ``SCITEX_AUDIO_ENV_SRC`` to load
all configuration from a ``.src`` file — this keeps ``.mcp.json`` static
across environments:

.. code-block:: json

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

Switch environments via your shell profile:

.. code-block:: bash

   # Local machine (has speakers)
   export SCITEX_AUDIO_ENV_SRC=~/.scitex/audio/local.src

   # Remote server (no speakers, uses relay)
   export SCITEX_AUDIO_ENV_SRC=~/.scitex/audio/remote.src

Generate a template ``.src`` file:

.. code-block:: bash

   scitex-audio show-env-template -o ~/.scitex/audio/local.src

Or install globally:

.. code-block:: bash

   scitex-audio mcp install
