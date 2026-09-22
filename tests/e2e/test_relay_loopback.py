#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2E: relay server round-trip on loopback (real HTTP subsystem, no network)."""

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.e2e

if os.environ.get("RUN_E2E") != "1":
    pytest.skip("e2e needs RUN_E2E=1 (real local subsystems)", allow_module_level=True)

_found = shutil.which("scitex-audio")
if _found is None:
    pytest.skip("scitex-audio console script not installed", allow_module_level=True)
CLI = str(_found)


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _start_relay():
    port = _free_port()
    proc = subprocess.Popen(
        [CLI, "relay", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("relay server exited during startup")
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as response:
                if response.status == 200:
                    return proc, base
        except OSError:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("relay server did not become healthy in time")


def _stop(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def _get_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_relay_health_reports_healthy():
    # Arrange
    proc, base = _start_relay()
    try:
        # Act
        _status, payload = _get_json(base + "/health")
        # Assert
        assert payload["status"] == "healthy"
    finally:
        _stop(proc)


def test_relay_list_backends_returns_backends_key():
    # Arrange
    proc, base = _start_relay()
    try:
        # Act
        _status, payload = _get_json(base + "/list_backends")
        # Assert
        assert "backends" in payload
    finally:
        _stop(proc)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
