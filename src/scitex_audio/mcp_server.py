#!/usr/bin/env python3
# Timestamp: "2026-02-06 23:03:14 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-audio/src/scitex_audio/mcp_server.py


# Timestamp: 2026-01-15

"""
FastMCP Server for SciTeX Audio - HTTP/SSE Transport Support

Enables remote agents to connect and play audio on local speakers.

Usage:
    scitex audio serve                           # stdio (default)
    scitex audio serve -t http --port 31293      # HTTP transport
    scitex audio serve -t sse --port 31293       # SSE transport

For remote audio:
    1. Run locally:  scitex audio serve -t http --port 31293
    2. SSH tunnel:   ssh -R 31293:localhost:31293 remote-host
    3. Remote agent connects to http://localhost:31293
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load environment variables from SCITEX_AUDIO_ENV_SRC early
from ._env_loader import load_scitex_audio_env

load_scitex_audio_env()

# Graceful FastMCP dependency handling
from scitex_dev import try_import_optional

FastMCP = try_import_optional(
    "fastmcp", attr="FastMCP", extra="mcp", pkg="scitex-audio"
)
FASTMCP_AVAILABLE = FastMCP is not None

__all__ = [
    "mcp",
    "run_server",
    "run_relay_server",
    "main",
    "FASTMCP_AVAILABLE",
]

# Import branding
from ._branding import get_mcp_instructions, get_mcp_server_name

# Initialize MCP server
if FASTMCP_AVAILABLE:
    mcp = FastMCP(
        name=get_mcp_server_name(),
        instructions=get_mcp_instructions(),
    )
else:
    mcp = None


def _get_audio_dir() -> Path:
    """Get the directory where generated TTS files are written.

    Returns ``~/.scitex/audio/runtime/tts/`` — under the ``runtime/``
    carve-out (the only untracked subtree of the audio state dir).
    """
    from ._state_paths import tts_output_dir

    return tts_output_dir()


if FASTMCP_AVAILABLE:
    import asyncio

    def _run_async(coro):
        """Run async handler synchronously for FastMCP tools."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    @mcp.tool()
    def audio_speak(
        text: str,
        backend: Optional[str] = None,
        voice: Optional[str] = None,
        rate: int = 150,
        speed: float = 1.5,
        play: bool = True,
        save: bool = False,
        fallback: bool = True,
        agent_id: Optional[str] = None,
        signature: bool = False,
    ) -> str:
        """Convert text to speech with fallback (elevenlabs -> luxtts -> gtts -> pyttsx3).

        Smart routing: Automatically uses relay when local audio unavailable.

        Routing logic (mode=auto, default):
        - If local audio sink is SUSPENDED and relay available -> uses relay
        - If local audio available -> uses local
        - If neither available -> returns error with instructions

        Environment variables:
        - SCITEX_AUDIO_MODE: 'local', 'remote', or 'auto' (default: auto)
        - SCITEX_AUDIO_RELAY_URL: Relay server URL for remote playback

        Args:
            text: Text to convert to speech
            backend: TTS backend (elevenlabs, luxtts, gtts, pyttsx3)
            voice: Voice/language
            rate: Speech rate (pyttsx3 only)
            speed: Speed multiplier for gtts (default 1.5)
            play: Play audio (default True)
            save: Save to file (default False)
            fallback: Try next backend on failure
            agent_id: Agent identifier for tracking
            signature: Prepend hostname/project/branch to text
        """
        from ._cross_process_lock import AudioPlaybackLock
        from ._speak import speak as tts_speak

        try:
            output_path = None
            if save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(_get_audio_dir() / f"tts_{timestamp}.mp3")

            # Prepend signature if requested
            final_text = text
            sig = None
            if signature:
                import os
                import socket
                import subprocess

                hostname = socket.gethostname()
                cwd = os.getcwd()
                project = os.path.basename(cwd)
                branch = None
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=cwd,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        branch = result.stdout.strip()
                except Exception:
                    pass

                parts = [hostname, project]
                if branch:
                    parts.append(branch)
                sig = ". ".join(parts) + ". "
                final_text = sig + text

            # Acquire cross-process lock for FIFO audio playback
            lock = AudioPlaybackLock()
            lock.acquire(timeout=120.0)
            try:
                speak_result = tts_speak(
                    text=final_text,
                    backend=backend,
                    voice=voice,
                    rate=rate,
                    speed=speed,
                    play=play,
                    output_path=output_path,
                    fallback=fallback,
                    # mode=None uses SCITEX_AUDIO_MODE env (default: auto)
                )
            finally:
                lock.release()

            result = {
                "success": speak_result.get("success", False),
                "text": text,
                "backend": speak_result.get("backend", backend),
                "played": speak_result.get("played", False),
                "play_requested": play,
                "mode": speak_result.get("mode", "unknown"),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            }

            if signature:
                result["signature"] = sig
                result["full_text"] = final_text
            if speak_result.get("path"):
                result["path"] = str(speak_result["path"])
            if speak_result.get("error"):
                result["error"] = speak_result["error"]
            if speak_result.get("routing"):
                result["routing"] = speak_result["routing"]
            if speak_result.get("local_state"):
                result["local_state"] = speak_result["local_state"]

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "text": text,
                },
                indent=2,
            )

    # Tool bodies live in `_mcp/server_tools.py` (importable + testable
    # without fastmcp). Each `@mcp.tool()` here is a thin wrapper whose
    # NAME matches its public `scitex_audio` Python counterpart so the
    # MCP surface stays 1:1 with the Python API (audit-mcp-tools §6).
    from ._mcp import server_tools as _st

    @mcp.tool()
    def audio_available_backends() -> str:
        """List available TTS backends and their status.

        Returns
        -------
            JSON string with available backends and fallback order
        """
        return _st.available_backends_tool()

    @mcp.tool()
    def audio_check_wsl_audio() -> str:
        """Check WSL audio connectivity and available playback methods.

        Returns
        -------
            JSON string with audio status information
        """
        return _st.check_wsl_audio_tool()

    @mcp.tool()
    def audio_check_local_audio_available() -> str:
        """Check whether local audio playback is usable on this host.

        Reports the PulseAudio sink state (RUNNING / IDLE / SUSPENDED /
        NO_SINK) and any WSL Windows fallback, so an agent can decide
        whether to play locally or route to a relay.

        Returns
        -------
            JSON string with the local-audio availability report
        """
        return _st.check_local_audio_available_tool()

    @mcp.tool()
    def audio_stop_speech() -> str:
        """Stop any currently playing speech.

        Returns
        -------
            JSON string confirming the stop request
        """
        return _st.stop_speech_tool()

    @mcp.tool()
    def audio_generate_bytes(
        text: str,
        backend: Optional[str] = None,
        voice: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate TTS audio to a file without playing it.

        Args:
            text: Text to synthesize
            backend: TTS backend (None -> fallback chain)
            voice: Voice/language override
            output_path: Explicit output file (None -> timestamped file
                in the audio runtime dir)

        Returns
        -------
            JSON string with the written path and byte count
        """
        return _st.generate_bytes_tool(
            text, backend=backend, voice=voice, output_path=output_path
        )

    @mcp.tool()
    def audio_announce_context(include_full_path: bool = False) -> str:
        """Announce the current working directory and git branch.

        Useful for orientation when starting work in a new session.

        Args:
            include_full_path: Include full path or just directory name

        Returns
        -------
            JSON string with context information and speak result
        """
        return _st.announce_context_tool(include_full_path=include_full_path)

    # Register STT tools
    from ._mcp.stt_handlers import register_stt_tools

    register_stt_tools(mcp)

    # §5 — skills introspection tools (per audit-mcp-tools convention)
    @mcp.tool()
    def audio_skills_list() -> str:
        """List the names of every skill page shipped by scitex-audio.

        Returns
        -------
            JSON string with `{"success": true, "package": "scitex-audio",
            "skills": ["01_quick-start", "02_available-backends", ...]}`.
        """
        try:
            skills_dir = Path(__file__).parent / "_skills" / "scitex-audio"
            names = sorted(
                p.stem for p in skills_dir.glob("*.md") if p.name != "SKILL.md"
            )
            return json.dumps(
                {"success": True, "package": "scitex-audio", "skills": names},
                indent=2,
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)

    @mcp.tool()
    def audio_skills_get(name: str) -> str:
        """Fetch the full Markdown content of one scitex-audio skill page.

        Args:
            name: Skill page name without `.md`, e.g. `01_quick-start`.

        Returns
        -------
            JSON string with `{"success": true, "package": "scitex-audio",
            "name": <name>, "content": <markdown>}`, or an error envelope.
        """
        try:
            skills_dir = Path(__file__).parent / "_skills" / "scitex-audio"
            target = skills_dir / f"{name}.md"
            if not target.exists():
                available = sorted(
                    p.stem for p in skills_dir.glob("*.md") if p.name != "SKILL.md"
                )
                return json.dumps(
                    {
                        "success": False,
                        "error": f"unknown skill {name!r}; available: {available}",
                    },
                    indent=2,
                )
            return json.dumps(
                {
                    "success": True,
                    "package": "scitex-audio",
                    "name": name,
                    "content": target.read_text(encoding="utf-8"),
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)


def run_server(
    transport: str = "stdio",
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Run the MCP server.

    Args:
        transport: Transport protocol ("stdio", "sse", or "http")
        host: Host for HTTP/SSE transport (default from branding)
        port: Port for HTTP/SSE transport (default from branding)
    """
    from ._branding import DEFAULT_HOST, DEFAULT_PORT

    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT

    if not FASTMCP_AVAILABLE:
        import sys

        from ._branding import BRAND_NAME

        print("=" * 60)
        print(f"MCP Server '{BRAND_NAME}' requires the 'fastmcp' package.")
        print()
        print("Install with:")
        print("  pip install fastmcp")
        print()
        print("Or install scitex with MCP support:")
        print("  pip install scitex[mcp]")
        print("=" * 60)
        sys.exit(1)

    from ._branding import BRAND_NAME

    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        print(f"Starting {BRAND_NAME} MCP server (SSE) on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "http":
        print(f"Starting {BRAND_NAME} MCP server (HTTP) on {host}:{port}")
        print(f"Connect via: http://{host}:{port}/mcp")
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}")


def run_relay_server(
    host: Optional[str] = None, port: Optional[int] = None, force: bool = False
) -> None:
    """Run HTTP relay server for remote audio playback.

    This exposes simple REST endpoints that remote agents can connect to.
    Unlike the MCP server, this uses standard HTTP POST/GET.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 31293)
        force: If True, kill any existing process using the port

    Endpoints:
        POST /speak - Speak text
        GET /health - Health check
        GET /list_backends - List available backends
    """
    from ._branding import BRAND_NAME, DEFAULT_HOST, DEFAULT_PORT

    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT

    if force:
        from ._utils import kill_process_on_port

        kill_process_on_port(port)

    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer
    except ImportError as e:
        raise RuntimeError(f"HTTP server not available: {e}") from e

    class RelayHandler(BaseHTTPRequestHandler):
        """HTTP handler for audio relay requests."""

        def _send_json(self, data: dict, status: int = 200) -> None:
            """Send JSON response."""
            import json

            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            """Handle CORS preflight."""
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self) -> None:
            """Handle GET requests."""
            import json

            if self.path == "/health":
                self._send_json({"status": "healthy", "server": BRAND_NAME})
            elif self.path == "/list_backends":
                result = list_backends()
                self._send_json(json.loads(result))
            else:
                self._send_json({"error": "Not found"}, 404)

        def do_POST(self) -> None:
            """Handle POST requests."""
            import json

            if self.path == "/speak":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body.decode("utf-8"))
                    # Import speak directly from audio module (not MCP tool)
                    from . import speak as tts_speak
                    from ._cross_process_lock import AudioPlaybackLock

                    # Acquire lock for FIFO
                    lock = AudioPlaybackLock()
                    lock.acquire(timeout=120.0)
                    try:
                        tts_speak(
                            text=data.get("text", ""),
                            backend=data.get("backend"),
                            voice=data.get("voice"),
                            rate=data.get("rate", 150),
                            speed=data.get("speed", 1.5),
                            play=data.get("play", True),
                            fallback=data.get("fallback", True),
                            mode="local",
                        )
                    finally:
                        lock.release()

                    self._send_json(
                        {
                            "success": True,
                            "text": data.get("text", ""),
                            "played": True,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except Exception as e:
                    self._send_json({"success": False, "error": str(e)}, 500)
            else:
                self._send_json({"error": "Not found"}, 404)

        def log_message(self, format: str, *args) -> None:
            """Suppress default logging."""
            pass

    print(f"Starting {BRAND_NAME} relay server on {host}:{port}")
    print("Endpoints: POST /speak, GET /health, GET /list_backends")
    server = HTTPServer((host, port), RelayHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down relay server")
        server.shutdown()


def main():
    """Entry point for scitex-audio-mcp command."""
    run_server(transport="stdio")


if __name__ == "__main__":
    main()

# EOF
