#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._system_deps (scitex_dev.system_deps provider)."""

import pytest

from scitex_audio import _system_deps


class TestDeclarations:
    def test_declares_ffmpeg_and_portaudio(self):
        packages = {dep.package for dep in _system_deps.declarations()}
        assert packages == {"ffmpeg", "portaudio19-dev"}

    def test_every_declaration_has_a_purpose(self):
        assert all(dep.purpose.strip() for dep in _system_deps.declarations())

    def test_no_extra_apt_repo_needed(self):
        # ffmpeg + portaudio19-dev are in the default Ubuntu repos.
        assert all(dep.apt_repo is None for dep in _system_deps.declarations())

    def test_provider_constant(self):
        assert _system_deps.PROVIDER == "scitex-audio"


class TestProvide:
    def test_provide_returns_systemdepspecs(self):
        # The keystone ships with newer scitex-dev; skip where unavailable.
        system_deps = pytest.importorskip("scitex_dev.system_deps")

        specs = _system_deps.provide()

        assert specs
        assert all(isinstance(s, system_deps.SystemDepSpec) for s in specs)
        assert {s.package for s in specs} == {"ffmpeg", "portaudio19-dev"}
        assert all(s.provider == "scitex-audio" for s in specs)

    def test_provide_matches_declarations(self):
        pytest.importorskip("scitex_dev.system_deps")

        declared = {(d.package, d.purpose, d.apt_repo) for d in _system_deps.declarations()}
        provided = {(s.package, s.purpose, s.apt_repo) for s in _system_deps.provide()}
        assert declared == provided


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
