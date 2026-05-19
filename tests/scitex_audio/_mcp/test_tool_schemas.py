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
    def test_returns_nonempty_list_schemas_is_list(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        schemas = _get_schemas()
        # Act
        # Assert
        assert isinstance(schemas, list)

    def test_returns_nonempty_list_len_schemas_0(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        schemas = _get_schemas()
        # Act
        # Assert
        assert len(schemas) > 0


    def test_every_schema_has_name(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        for s in _get_schemas():
            assert isinstance(s["name"], str) and s["name"], s

    def test_every_schema_has_description(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        for s in _get_schemas():
            assert (isinstance(s['description'], str) and s['description']) and (len(s['description']) >= 10)

    def test_every_schema_has_input_schema_object(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        for s in _get_schemas():
            isch = s["inputSchema"]
            assert (isinstance(isch, dict)) and (isch.get('type') == 'object') and ('properties' in isch) and (isinstance(isch['properties'], dict))

    def test_required_fields_exist_in_properties(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        for s in _get_schemas():
            isch = s["inputSchema"]
            for req in isch.get("required", []) or []:
                assert req in isch["properties"], (
                    f"{s['name']}: required field `{req}` missing from properties"
                )

    def test_names_are_unique(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        names = [s["name"] for s in _get_schemas()]
        # Assert
        assert len(names) == len(set(names))


class TestExpectedTools:
    def test_all_expected_names_present(self):
        # Arrange
        names = {s["name"] for s in _get_schemas()}
        # Act
        missing = EXPECTED_NAMES - names
        # Assert
        assert not missing, f"missing expected tool names: {sorted(missing)}"

    def test_speak_requires_text_text_in_s_inputschema_get_required(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        s = next(s for s in _get_schemas() if s["name"] == "speak")
        # Act
        # Assert
        assert "text" in s["inputSchema"].get("required", [])

    def test_speak_requires_text_s_inputschema_properties_text_type_string(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        s = next(s for s in _get_schemas() if s["name"] == "speak")
        # Act
        # Assert
        assert s["inputSchema"]["properties"]["text"]["type"] == "string"


    def test_play_audio_requires_path(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        s = next(s for s in _get_schemas() if s["name"] == "play_audio")
        # Assert
        assert "path" in s["inputSchema"].get("required", [])

    def test_generate_audio_requires_text(self):
        # Arrange
        # Act
        # Arrange
        # Act
        # Arrange
        # Act
        s = next(s for s in _get_schemas() if s["name"] == "generate_audio")
        # Assert
        assert "text" in s["inputSchema"].get("required", [])


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])

# EOF
