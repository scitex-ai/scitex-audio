"""STT setup paths are discoverable through the owning environment registry."""

import pytest

from scitex_audio._env_registry import generate_template, get_env_docs


@pytest.mark.parametrize("name", ["SCITEX_AUDIO_WHISPER_CLI", "SCITEX_AUDIO_WHISPER_MODEL"])
def test_stt_paths_are_registered_without_a_model_name_default(name):
    # Arrange
    expected = ("stt", None)
    # Act
    entry = get_env_docs()[name]
    # Assert
    assert (entry["module"], entry["default"]) == expected


@pytest.mark.parametrize("name", ["SCITEX_AUDIO_WHISPER_CLI", "SCITEX_AUDIO_WHISPER_MODEL"])
def test_stt_paths_are_in_the_generated_setup_template(name):
    # Arrange
    expected = f"# export {name}="
    # Act
    template = generate_template(include_sensitive=False)
    # Assert
    assert expected in template
