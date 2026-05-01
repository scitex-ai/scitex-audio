#!/usr/bin/env python3
"""scitex-audio quickstart (offline-safe).

Imports the package and queries available backends without
performing any network calls or audio output. Suitable for CI smoke tests.
"""

from __future__ import annotations

import scitex_audio as sxa


def main() -> int:
    backends = sxa.available_backends()
    print(f"Available TTS backends: {backends}")

    models = sxa.available_models()
    print(f"Available STT (whisper) models: {models}")

    print("scitex-audio import + introspection OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
