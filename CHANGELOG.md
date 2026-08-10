# Changelog

All notable changes to `scitex-audio` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **stt**: optional `faster-whisper` (CTranslate2) backend alongside the
  existing whisper.cpp CLI backend, plus a backend-selection layer in
  `_stt.py` (`transcribe(..., backend=...)` /
  `SCITEX_AUDIO_STT_BACKEND`). Install with
  `pip install 'scitex-audio[faster-whisper]'`.

  `auto` keeps whisper.cpp when its binary **and** a model both resolve —
  an existing working setup does not change engines underfoot — and
  otherwise uses faster-whisper.

  Measured on a GTX 1070 (sm_61) with `large-v3` + `int8`: CUDA
  transcribe 1.46 s vs CPU 21.60 s (~15x). Device detection asks
  CTranslate2, never `torch`: on Pascal `torch.cuda.is_available()`
  returns True while the wheel ships no sm_61 kernel, so a torch-based
  check would promise a GPU that cannot run. Unlike the whisper.cpp path,
  this backend decodes via PyAV and needs no `ffmpeg` binary.

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
