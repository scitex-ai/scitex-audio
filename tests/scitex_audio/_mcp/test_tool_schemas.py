#!/usr/bin/env python3
"""Tests for scitex_audio._mcp.tool_schemas (MCP tool schema definitions).

Each schema must:
  - have a non-empty `name` (string)
  - have a non-empty `description` (string) — agents key off this
  - have an `inputSchema` dict with `type: "object"` and a `properties` map
  - if `required` is present, every required key must exist in `properties`
"""

import pytest


def _get_schemas():
    """Load schemas as plain dicts for inspection.

    `mcp.types.Tool` may or may not be installed depending on the test
    environment; we work with .model_dump() / dict(...) where possible
    and fall back to attribute access.
    """
    from scitex_audio._mcp.tool_schemas import get_tool_schemas

    schemas = get_tool_schemas()
    out = []
    for s in schemas:
        if hasattr(s, "model_dump"):
            out.append(s.model_dump())
        elif isinstance(s, dict):
            out.append(s)
        else:
            out.append(
                {
                    "name": getattr(s, "name", None),
                    "description": getattr(s, "description", None),
                    "inputSchema": getattr(s, "inputSchema", None),
                }
            )
    return out


# Agent-facing tool names that must be exported (kept in lock-step with handlers.py).
EXPECTED_NAMES = {
    "speak",
    "generate_audio",
    "list_backends",
    "list_voices",
    "play_audio",
    "list_audio_files",
    "clear_audio_cache",
    "speech_queue_status",
    "check_audio_status",
    "announce_context",
}


class TestToolSchemaShape:
    def test_returns_nonempty_list(self):
        schemas = _get_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0

    def test_every_schema_has_name(self):
        for s in _get_schemas():
            assert isinstance(s["name"], str) and s["name"], s

    def test_every_schema_has_description(self):
        for s in _get_schemas():
            assert isinstance(s["description"], str) and s["description"], s
            # Non-trivial description (agents need something to discriminate on).
            assert len(s["description"]) >= 20, s

    def test_every_schema_has_input_schema_object(self):
        for s in _get_schemas():
            isch = s["inputSchema"]
            assert isinstance(isch, dict), s
            assert isch.get("type") == "object", s
            assert "properties" in isch, s
            assert isinstance(isch["properties"], dict), s

    def test_required_fields_exist_in_properties(self):
        for s in _get_schemas():
            isch = s["inputSchema"]
            for req in isch.get("required", []) or []:
                assert req in isch["properties"], (
                    f"{s['name']}: required field `{req}` missing from properties"
                )

    def test_names_are_unique(self):
        names = [s["name"] for s in _get_schemas()]
        assert len(names) == len(set(names))


class TestExpectedTools:
    def test_all_expected_names_present(self):
        names = {s["name"] for s in _get_schemas()}
        missing = EXPECTED_NAMES - names
        assert not missing, f"missing expected tool names: {sorted(missing)}"

    def test_speak_requires_text(self):
        s = next(s for s in _get_schemas() if s["name"] == "speak")
        assert "text" in s["inputSchema"].get("required", [])
        # `text` should be a string field
        assert s["inputSchema"]["properties"]["text"]["type"] == "string"

    def test_play_audio_requires_path(self):
        s = next(s for s in _get_schemas() if s["name"] == "play_audio")
        assert "path" in s["inputSchema"].get("required", [])

    def test_generate_audio_requires_text(self):
        s = next(s for s in _get_schemas() if s["name"] == "generate_audio")
        assert "text" in s["inputSchema"].get("required", [])


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
