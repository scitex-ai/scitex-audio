#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._relay and the MCP speak handlers.

No mocks: the relay client talks to a real in-process http.server bound to a
free port; environment variables use yield-based save/restore fixtures; the
speak handlers take injectable resolver / TTS-function / sink-probe seams.
"""

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from scitex_audio._branding import get_relay_url, get_ssh_client_ip
from scitex_audio._mcp.speak_handlers import (
    speak_local_handler,
    speak_relay_handler,
)
from scitex_audio._relay import (
    RelayClient,
    get_relay_client,
    reset_relay_client,
)


@pytest.fixture
def env_save_restore():
    """Snapshot the relay/SSH/audio env vars; restore on teardown."""
    keys = (
        "SCITEX_AUDIO_RELAY_URL",
        "SCITEX_AUDIO_RELAY_HOST",
        "SCITEX_AUDIO_RELAY_PORT",
        "SCITEX_AUDIO_MODE",
        "SSH_CLIENT",
        "SSH_CONNECTION",
    )
    saved = {k: os.environ.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@pytest.fixture
def relay_server():
    """Real in-process HTTP relay server on a free port."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            if self.path == "/health":
                self._respond(200, {"status": "healthy"})
            elif self.path == "/list_backends":
                self._respond(200, {"backends": ["gtts", "pyttsx3"]})
            else:
                self._respond(404, {"error": "not found"})

        def do_POST(self):
            if self.path == "/speak":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                self._respond(200, {"success": True, "text": body.get("text")})
            else:
                self._respond(404, {"error": "not found"})

        def _respond(self, status, data):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()


class TestRelayClientInit:
    def test_init_stores_base_url(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999")
        # Assert
        assert client.base_url == "http://localhost:9999"

    def test_init_default_timeout_is_30(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999")
        # Assert
        assert client.timeout == 30

    def test_trailing_slash_is_stripped(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999/")
        # Assert
        assert client.base_url == "http://localhost:9999"

    def test_custom_timeout_is_stored(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999", timeout=60)
        # Assert
        assert client.timeout == 60

    def test_url_auto_detected_from_env(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_RELAY_URL"] = "http://auto-detected:31293"
        # Act
        client = RelayClient()
        # Assert
        assert client.base_url == "http://auto-detected:31293"


class TestRelayClientMethods:
    def test_health_reports_healthy(self, relay_server):
        # Arrange
        client = RelayClient(relay_server, timeout=5)
        # Act
        result = client.health()
        # Assert
        assert result["status"] == "healthy"

    def test_is_available_true_when_server_up(self, relay_server):
        # Arrange
        client = RelayClient(relay_server, timeout=5)
        # Act
        result = client.is_available()
        # Assert
        assert result is True

    def test_is_available_false_when_unreachable(self):
        # Arrange — a port with no listener gives a real connection refusal
        client = RelayClient("http://127.0.0.1:59999", timeout=1)
        # Act
        result = client.is_available()
        # Assert
        assert result is False

    def test_speak_reports_success(self, relay_server):
        # Arrange
        client = RelayClient(relay_server, timeout=5)
        # Act
        result = client.speak("Hello test")
        # Assert
        assert result["success"] is True

    def test_speak_echoes_text(self, relay_server):
        # Arrange
        client = RelayClient(relay_server, timeout=5)
        # Act
        result = client.speak("Hello test")
        # Assert
        assert result["text"] == "Hello test"

    def test_list_backends_returns_backends(self, relay_server):
        # Arrange
        client = RelayClient(relay_server, timeout=5)
        # Act
        result = client.list_backends()
        # Assert
        assert result["backends"] == ["gtts", "pyttsx3"]


class TestModuleFunctions:
    def test_get_relay_client_returns_singleton(self):
        # Arrange
        reset_relay_client()
        first = get_relay_client("http://test:1234")
        # Act
        second = get_relay_client()
        # Assert
        assert first is second

    def test_reset_creates_new_instance(self):
        # Arrange
        first = get_relay_client("http://test:1234")
        reset_relay_client()
        # Act
        second = get_relay_client("http://test:5678")
        # Assert
        assert first is not second

    def test_new_instance_uses_new_url(self):
        # Arrange
        get_relay_client("http://test:1234")
        reset_relay_client()
        # Act
        second = get_relay_client("http://test:5678")
        # Assert
        assert second.base_url == "http://test:5678"


class TestBrandingSshDetection:
    def test_ssh_client_ip_from_ssh_client_var(self, env_save_restore):
        # Arrange
        os.environ["SSH_CLIENT"] = "192.168.1.100 54321 22"
        # Act
        ip = get_ssh_client_ip()
        # Assert
        assert ip == "192.168.1.100"

    def test_ssh_client_ip_from_ssh_connection_var(self, env_save_restore):
        # Arrange
        os.environ.pop("SSH_CLIENT", None)
        os.environ["SSH_CONNECTION"] = "10.0.0.50 54321 10.0.0.1 22"
        # Act
        ip = get_ssh_client_ip()
        # Assert
        assert ip == "10.0.0.50"

    def test_ssh_client_ip_none_outside_ssh(self, env_save_restore):
        # Arrange
        os.environ.pop("SSH_CLIENT", None)
        os.environ.pop("SSH_CONNECTION", None)
        # Act
        ip = get_ssh_client_ip()
        # Assert
        assert ip is None

    def test_relay_url_from_url_var(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_RELAY_URL"] = "http://custom:8080"
        # Act
        url = get_relay_url()
        # Assert
        assert url == "http://custom:8080"

    def test_relay_url_built_from_host_and_port(self, env_save_restore):
        # Arrange
        os.environ.pop("SCITEX_AUDIO_RELAY_URL", None)
        os.environ["SCITEX_AUDIO_RELAY_HOST"] = "myhost"
        os.environ["SCITEX_AUDIO_RELAY_PORT"] = "9999"
        # Act
        url = get_relay_url()
        # Assert
        assert url == "http://myhost:9999"


class TestSpeakLocalHandler:
    def test_play_false_reports_success(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        fake_speak = lambda **kw: {  # noqa: E731
            "success": True,
            "played": False,
            "play_requested": False,
            "backend": "gtts",
            "mode": "local",
        }
        # Act
        result = asyncio.run(
            speak_local_handler("Test text", play=False, speak_fn=fake_speak)
        )
        # Assert
        assert result["success"] is True

    def test_play_false_marks_played_on_server(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        fake_speak = lambda **kw: {"success": True, "played": False}  # noqa: E731
        # Act
        result = asyncio.run(
            speak_local_handler("Test text", play=False, speak_fn=fake_speak)
        )
        # Assert
        assert result["played_on"] == "server"

    def test_mode_remote_fails(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "remote"
        # Act
        result = asyncio.run(speak_local_handler("Test text"))
        # Assert
        assert result["success"] is False

    def test_mode_remote_error_mentions_mode(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "remote"
        # Act
        result = asyncio.run(speak_local_handler("Test text"))
        # Assert
        assert "SCITEX_AUDIO_MODE=remote" in result["error"]

    def test_suspended_sink_fails(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        suspended = lambda: {  # noqa: E731
            "available": False,
            "state": "SUSPENDED",
            "reason": "No output",
        }
        # Act
        result = asyncio.run(
            speak_local_handler("Test text", play=True, sink_check=suspended)
        )
        # Assert
        assert result["success"] is False

    def test_suspended_sink_reports_state(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        suspended = lambda: {  # noqa: E731
            "available": False,
            "state": "SUSPENDED",
            "reason": "No output",
        }
        # Act
        result = asyncio.run(
            speak_local_handler("Test text", play=True, sink_check=suspended)
        )
        # Assert
        assert result.get("sink_state") == "SUSPENDED"


class TestSpeakRelayHandler:
    def test_no_url_fails(self):
        # Arrange — resolvers report no relay configured
        # Act
        result = asyncio.run(
            speak_relay_handler(
                "Test",
                url_resolver=lambda: None,
                ssh_ip_resolver=lambda: None,
            )
        )
        # Assert
        assert result["success"] is False

    def test_no_url_error_mentions_not_configured(self):
        # Arrange
        # Act
        result = asyncio.run(
            speak_relay_handler(
                "Test",
                url_resolver=lambda: None,
                ssh_ip_resolver=lambda: None,
            )
        )
        # Assert
        assert "not configured" in result["error"].lower()

    def test_no_url_includes_setup_instructions(self):
        # Arrange
        # Act
        result = asyncio.run(
            speak_relay_handler(
                "Test",
                url_resolver=lambda: None,
                ssh_ip_resolver=lambda: None,
            )
        )
        # Assert
        assert "instructions" in result

    def test_forwards_to_real_relay_server(self, relay_server):
        # Arrange
        # Act
        result = asyncio.run(
            speak_relay_handler(
                "Hello relay",
                url_resolver=lambda: relay_server,
                ssh_ip_resolver=lambda: None,
            )
        )
        # Assert
        assert result["played_on"] == "relay"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
