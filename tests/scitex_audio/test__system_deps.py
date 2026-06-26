#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_audio._system_deps (scitex_dev.system_deps provider)."""

import pytest

from scitex_audio import _system_deps


class TestDeclarations:
    def test_declares_ffmpeg_and_portaudio_packages(self):
        # Arrange
        declared = _system_deps.declarations()
        # Act
        packages = {dep.package for dep in declared}
        # Assert
        assert packages == {"ffmpeg", "portaudio19-dev"}

    def test_every_declaration_has_nonempty_purpose(self):
        # Arrange
        declared = _system_deps.declarations()
        # Act
        purposes = [dep.purpose.strip() for dep in declared]
        # Assert
        assert all(purposes)

    def test_declarations_need_no_extra_apt_repo(self):
        # Arrange
        declared = _system_deps.declarations()
        # Act
        repos = [dep.apt_repo for dep in declared]
        # Assert
        assert all(repo is None for repo in repos)

    def test_provider_constant_is_scitex_audio(self):
        # Arrange
        expected = "scitex-audio"
        # Act
        provider = _system_deps.PROVIDER
        # Assert
        assert provider == expected


class TestProvide:
    def test_provide_returns_only_systemdepspec_instances(self):
        # Arrange
        system_deps = pytest.importorskip("scitex_dev.system_deps")
        # Act
        specs = _system_deps.provide()
        # Assert
        assert all(isinstance(spec, system_deps.SystemDepSpec) for spec in specs)

    def test_provide_exposes_both_apt_packages(self):
        # Arrange
        pytest.importorskip("scitex_dev.system_deps")
        # Act
        specs = _system_deps.provide()
        # Assert
        assert {spec.package for spec in specs} == {"ffmpeg", "portaudio19-dev"}

    def test_provide_tags_every_spec_with_provider(self):
        # Arrange
        pytest.importorskip("scitex_dev.system_deps")
        # Act
        specs = _system_deps.provide()
        # Assert
        assert all(spec.provider == "scitex-audio" for spec in specs)

    def test_provide_matches_local_declarations(self):
        # Arrange
        pytest.importorskip("scitex_dev.system_deps")
        declared = {
            (dep.package, dep.purpose, dep.apt_repo)
            for dep in _system_deps.declarations()
        }
        # Act
        provided = {
            (spec.package, spec.purpose, spec.apt_repo)
            for spec in _system_deps.provide()
        }
        # Assert
        assert provided == declared


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# EOF
