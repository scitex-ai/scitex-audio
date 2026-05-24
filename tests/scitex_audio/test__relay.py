#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._relay module.

Mock-free rewrite. Network endpoints are exercised against a real
in-process `http.server` (already used by the prior file); every
remaining `patch(...)` / `patch.dict(os.environ, ...)` is replaced
with a hand-rolled instance swap (`client.health = lambda: ...`),
a yield-based env-var snapshot/restore fixture, or a module
attribute swap that restores on teardown.
"""

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import scitex_audio
import scitex_audio._branding as _branding
import scitex_audio._mcp.speak_handlers as _speak_handlers
import scitex_audio._relay as _relay
from scitex_audio._mcp.speak_handlers import (
    speak_local_handler,
    speak_relay_handler,
)
from scitex_audio._relay import (
    RelayClient,
    get_relay_client,
    reset_relay_client,
)

_ENV_KEYS = (
    "SCITEX_AUDIO_MODE",
    "SCITEX_AUDIO_RELAY_URL",
    "SCITEX_AUDIO_RELAY_HOST",
    "SCITEX_AUDIO_RELAY_PORT",
    "SSH_CLIENT",
    "SSH_CONNECTION",
)


@pytest.fixture
def env_save_restore():
    """Snapshot the env keys this file touches; restore on teardown."""
    saved = {k: os.environ.get(k) for k in _ENV_KEYS}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@pytest.fixture
def mock_server():
    """In-process HTTP server; exposes /health, /list_backends, /speak."""

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002 - stdlib API
            pass

        def do_GET(self):  # noqa: N802 - stdlib API
            if self.path == "/health":
                self._respond(200, {"status": "healthy"})
            elif self.path == "/list_backends":
                self._respond(200, {"backends": ["gtts", "pyttsx3"]})
            else:
                self._respond(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802 - stdlib API
            if self.path == "/speak":
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length))
                self._respond(200, {"success": True, "text": body.get("text")})
            else:
                self._respond(404, {"error": "not found"})

        def _respond(self, status, data):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


class TestRelayClient:
    """Tests for RelayClient class."""

    def test_init_with_url_stores_base_url(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999")
        # Assert
        assert client.base_url == "http://localhost:9999"

    def test_init_default_timeout_is_thirty(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999")
        # Assert
        assert client.timeout == 30

    def test_init_strips_trailing_slash_from_url(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999/")
        # Assert
        assert client.base_url == "http://localhost:9999"

    def test_init_custom_timeout_is_preserved(self):
        # Arrange
        # Act
        client = RelayClient("http://localhost:9999", timeout=60)
        # Assert
        assert client.timeout == 60

    def test_init_with_no_url_auto_detects_from_swapped_module(self, env_save_restore):
        # Arrange — swap the module-level get_relay_url with a fake.
        real = _relay.get_relay_url
        _relay.get_relay_url = lambda: "http://auto-detected:31293"
        try:
            # Act
            client = RelayClient()
        finally:
            _relay.get_relay_url = real
        # Assert
        assert client.base_url == "http://auto-detected:31293"


class TestRelayClientMethods:
    """Tests for RelayClient methods against an in-process HTTP server."""

    def test_health_check_returns_healthy_status(self, mock_server):
        # Arrange
        client = RelayClient(mock_server, timeout=5)
        # Act
        result = client.health()
        # Assert
        assert result["status"] == "healthy"

    def test_is_available_returns_true_when_server_responds(self, mock_server):
        # Arrange
        client = RelayClient(mock_server, timeout=5)
        # Act
        value = client.is_available()
        # Assert
        assert value is True

    def test_is_available_returns_false_when_health_raises(self):
        # Arrange — swap the instance's health() with a failing callable.
        client = RelayClient("http://127.0.0.1:59999", timeout=1)

        def _raise():
            raise ConnectionError("unreachable")

        client.health = _raise
        # Act
        value = client.is_available()
        # Assert
        assert value is False

    def test_speak_returns_success_true_from_server(self, mock_server):
        # Arrange
        client = RelayClient(mock_server, timeout=5)
        # Act
        result = client.speak("Hello test")
        # Assert
        assert result["success"] is True

    def test_speak_echoes_text_back_from_server(self, mock_server):
        # Arrange
        client = RelayClient(mock_server, timeout=5)
        # Act
        result = client.speak("Hello test")
        # Assert
        assert result["text"] == "Hello test"

    def test_list_backends_response_contains_backends_key(self, mock_server):
        # Arrange
        client = RelayClient(mock_server, timeout=5)
        # Act
        result = client.list_backends()
        # Assert
        assert "backends" in result


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_relay_client_is_singleton_across_calls(self):
        # Arrange
        reset_relay_client()
        client1 = get_relay_client("http://test:1234")
        # Act
        client2 = get_relay_client()
        # Assert
        assert client1 is client2

    def test_reset_relay_client_returns_new_instance(self):
        # Arrange
        client1 = get_relay_client("http://test:1234")
        reset_relay_client()
        # Act
        client2 = get_relay_client("http://test:5678")
        # Assert
        assert client1 is not client2

    def test_reset_relay_client_uses_new_base_url(self):
        # Arrange
        get_relay_client("http://test:1234")
        reset_relay_client()
        # Act
        client2 = get_relay_client("http://test:5678")
        # Assert
        assert client2.base_url == "http://test:5678"


class TestBrandingFunctions:
    """Tests for _branding module relay functions."""

    def test_get_ssh_client_ip_reads_from_ssh_client_var(self, env_save_restore):
        # Arrange
        os.environ.pop("SSH_CONNECTION", None)
        os.environ["SSH_CLIENT"] = "192.168.1.100 54321 22"
        # Act
        value = _branding.get_ssh_client_ip()
        # Assert
        assert value == "192.168.1.100"

    def test_get_ssh_client_ip_falls_back_to_ssh_connection_var(self, env_save_restore):
        # Arrange
        os.environ.pop("SSH_CLIENT", None)
        os.environ["SSH_CONNECTION"] = "10.0.0.50 54321 10.0.0.1 22"
        # Act
        value = _branding.get_ssh_client_ip()
        # Assert
        assert value == "10.0.0.50"

    def test_get_ssh_client_ip_returns_none_when_no_ssh_env(self, env_save_restore):
        # Arrange
        os.environ.pop("SSH_CLIENT", None)
        os.environ.pop("SSH_CONNECTION", None)
        # Act
        value = _branding.get_ssh_client_ip()
        # Assert
        assert value is None

    def test_get_relay_url_reads_from_relay_url_env_var(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_RELAY_URL"] = "http://custom:8080"
        # Act
        value = _branding.get_relay_url()
        # Assert
        assert value == "http://custom:8080"

    def test_get_relay_url_builds_from_host_and_port_env(self, env_save_restore):
        # Arrange
        os.environ.pop("SCITEX_AUDIO_RELAY_URL", None)
        os.environ["SCITEX_AUDIO_RELAY_HOST"] = "myhost"
        os.environ["SCITEX_AUDIO_RELAY_PORT"] = "9999"
        # Act
        value = _branding.get_relay_url()
        # Assert
        assert value == "http://myhost:9999"


class TestSpeakHandlers:
    """Tests for speak handlers."""

    def test_speak_local_handler_returns_success_when_play_false(
        self, env_save_restore
    ):
        # Arrange — swap scitex_audio.speak with a recorder; force MODE=local.
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        mock_result = {
            "success": True,
            "played": False,
            "play_requested": False,
            "backend": "gtts",
            "mode": "local",
        }
        real_speak = scitex_audio.speak
        scitex_audio.speak = lambda **_: mock_result
        try:
            # Act
            result = asyncio.run(speak_local_handler("Test text", play=False))
        finally:
            scitex_audio.speak = real_speak
        # Assert
        assert result["success"] is True

    def test_speak_local_handler_reports_server_as_played_on(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        mock_result = {
            "success": True,
            "played": False,
            "play_requested": False,
            "backend": "gtts",
            "mode": "local",
        }
        real_speak = scitex_audio.speak
        scitex_audio.speak = lambda **_: mock_result
        try:
            # Act
            result = asyncio.run(speak_local_handler("Test text", play=False))
        finally:
            scitex_audio.speak = real_speak
        # Assert
        assert result["played_on"] == "server"

    def test_speak_local_handler_refuses_when_mode_is_remote(self, env_save_restore):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "remote"
        # Act
        result = asyncio.run(speak_local_handler("Test text"))
        # Assert
        assert result["success"] is False

    def test_speak_local_handler_remote_mode_error_mentions_env_var(
        self, env_save_restore
    ):
        # Arrange
        os.environ["SCITEX_AUDIO_MODE"] = "remote"
        # Act
        result = asyncio.run(speak_local_handler("Test text"))
        # Assert
        assert "SCITEX_AUDIO_MODE=remote" in result["error"]

    def test_speak_local_handler_fails_when_sink_suspended(self, env_save_restore):
        # Arrange — replace check_audio_sink_state with a fake suspended sink.
        os.environ["SCITEX_AUDIO_MODE"] = "local"
        real_check = _speak_handlers.check_audio_sink_state
        _speak_handlers.check_audio_sink_state = lambda: {
            "available": False,
            "state": "SUSPENDED",
            "reason": "No output",
        }
        try:
            # Act
            result = asyncio.run(speak_local_handler("Test text", play=True))
        finally:
            _speak_handlers.check_audio_sink_state = real_check
        # Assert
        assert result["sink_state"] == "SUSPENDED"

    def test_speak_relay_handler_returns_error_when_no_url_configured(
        self, env_save_restore
    ):
        # Arrange — swap module-level get_relay_url + get_ssh_client_ip.
        real_get_url = _branding.get_relay_url
        real_get_ip = _branding.get_ssh_client_ip
        _branding.get_relay_url = lambda: None
        _branding.get_ssh_client_ip = lambda: None
        try:
            # Act
            result = asyncio.run(speak_relay_handler("Test"))
        finally:
            _branding.get_relay_url = real_get_url
            _branding.get_ssh_client_ip = real_get_ip
        # Assert
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
