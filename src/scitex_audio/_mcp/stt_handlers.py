#!/usr/bin/env python3
# Timestamp: "2026-03-26 (ywatanabe)"
# File: scitex-audio/src/scitex_audio/_mcp/stt_handlers.py

"""STT (Speech-to-Text) handlers for scitex.audio MCP server.

Provides audio_transcribe and list_whisper_models tool functions
that delegate to the _stt module.
"""

import json
from datetime import datetime
from typing import Optional

__all__ = [
    "register_stt_tools",
]


def register_stt_tools(mcp) -> None:
    """Register STT tools on the given FastMCP server instance.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.tool()
    def audio_transcribe(
        audio_path: str,
        language: Optional[str] = "ja",
        model: str = "tiny",
    ) -> str:
        """Transcribe audio file to text using whisper.cpp.

        Converts any audio format (via ffmpeg) and runs whisper-cli locally.

        Args:
            audio_path: Path to audio file (WAV, MP3, OGG, etc.)
            language: Language code (e.g., "ja", "en"). None for auto-detect.
            model: Whisper model name (tiny, base, small, medium, large-v3-turbo)

        Returns:
            JSON string with transcription result
        """
        try:
            from .._stt import transcribe

            result = transcribe(
                audio_path=audio_path,
                language=language,
                model=model,
            )
            result["timestamp"] = datetime.now().isoformat()
            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "audio_path": audio_path,
                },
                indent=2,
            )

    @mcp.tool()
    def list_whisper_models() -> str:
        """List available whisper models for speech-to-text.

        Returns:
            JSON string with available model names and whisper-cli status
        """
        try:
            from .._stt import available_models, find_whisper_cli

            cli = find_whisper_cli()
            models = available_models()

            return json.dumps(
                {
                    "success": True,
                    "whisper_cli": cli,
                    "whisper_cli_available": cli is not None,
                    "available_models": models,
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)


# EOF
