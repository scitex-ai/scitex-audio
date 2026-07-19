# Changelog

All notable changes to `scitex-audio` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **elevenlabs**: default to the low-latency `eleven_turbo_v2_5` model
  instead of `eleven_multilingual_v2`, which was noticeably slow for the
  short notification blurbs this package mostly speaks. Override with
  `SCITEX_AUDIO_ELEVENLABS_MODEL` (e.g. `eleven_flash_v2_5` for the
  lowest latency, `eleven_multilingual_v2` for the highest quality).

### Fixed

- **elevenlabs**: the model default lived in two places — `TTSConfig`
  passed its own `eleven_multilingual_v2` straight through, so a new
  engine default could never take effect on the `TTS` path. Resolution
  now happens once in `resolve_model_id()` (explicit > env > default)
  and `TTSConfig.model_id` defaults to `None`.
- **repo**: gitignore `.envrc` and `.worktrees/`; both had been swept
  into rescue autosave commits on `develop`.

## [0.3.0]

### Added

- **system-deps**: declare scitex-audio's OS-level apt dependencies
  (`ffmpeg`, `portaudio19-dev`) via the `scitex_dev.system_deps`
  entry-point so `scitex-dev ecosystem system-deps` federates them at
  container-build time instead of hardcoding the apt list. Adds the
  `scitex-audio dev system-deps list|install` verb-group (install is
  BUILD-time/root; dry-run by default).

## [0.2.13]

### Fixed

- **mcp**: align MCP tools 1:1 with public Python API (audit §6
  parity). Adds missing tool wrappers and removes orphaned ones so
  `scitex-dev ecosystem audit-mcp-tools scitex-audio` is clean.
- **relay**: correct `RelayClient.is_available()` reachability check —
  it no longer reports available against an unresponsive endpoint.
- **state-dir**: write ephemeral artifacts under
  `<scitex-dir>/audio/runtime/` carve-out so they are excluded from
  the user-data state directory.

### Changed

- **tests**: complete de-mock pass across handlers / tts / cli /
  engines / lock / relay; drives `scitex-dev ecosystem audit-all
  scitex-audio` PA-306 + PA-307 violations to 0. Production now
  exposes injectable seams (`engine=` on `SystemTTS`, `runner=` on
  `_play_audio`, `lock_file=` on `acquire_audio_lock`) so tests run
  against real collaborators without `unittest.mock`.
- **cli**: split oversized `_cli/_main.py` into per-command modules
  under `_cli/_commands/` (later consolidated back); tests rewritten
  to exercise the command surface directly.
- **ci(docs)**: make the `_sphinx_html` commit-back step non-fatal
  so a sphinx-out hiccup never blocks a release.
- **ci(codecov)**: disable PR comments to stop email noise.

## [0.2.10]

- Initial CHANGELOG entry — see git log for prior history.
