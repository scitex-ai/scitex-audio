# Changelog

All notable changes to `scitex-audio` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
