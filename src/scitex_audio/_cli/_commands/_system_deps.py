#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``dev system-deps`` command group for the ``scitex-audio`` CLI.

Exposes scitex-audio's own ``scitex_dev.system_deps`` provider as the uniform
``scitex-<pkg> dev system-deps list|install`` surface (mirrors
``scitex-dev ecosystem system-deps``). ``list`` is pipe-friendly; ``install``
is BUILD-time only (apt needs root; agents run rootless ``--userns``).
"""

from __future__ import annotations

import click

from scitex_audio import _system_deps


def _declared():
    return _system_deps.declarations()


def _render(deps) -> None:
    """Human-readable table of this package's declarations."""
    from rich.console import Console
    from rich.table import Table

    if not deps:
        Console().print("[yellow]scitex-audio declares no system deps.[/yellow]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("package")
    table.add_column("provider")
    table.add_column("purpose")
    table.add_column("apt_repo")
    for dep in deps:
        table.add_row(
            dep.package, _system_deps.PROVIDER, dep.purpose, dep.apt_repo or "-"
        )
    Console().print(table)
    Console().print(f"[bold]{len(deps)}[/bold] system package(s) for scitex-audio.")


def _emit_json(deps) -> None:
    import json as _json

    click.echo(
        _json.dumps(
            [
                {
                    "package": dep.package,
                    "purpose": dep.purpose,
                    "provider": _system_deps.PROVIDER,
                    "apt_repo": dep.apt_repo,
                }
                for dep in deps
            ],
            indent=2,
        )
    )


def _do_install(deps, *, dry_run: bool) -> int:
    """apt-get install scitex-audio's set (BUILD-time; needs root).

    Previews the exact apt commands when ``dry_run`` is set (the default unless
    ``--yes`` is given).
    """
    import os
    import subprocess

    if not deps:
        click.echo("scitex-audio declares no system deps; nothing to install.")
        return 0

    repos = sorted({dep.apt_repo for dep in deps if dep.apt_repo})
    packages = [dep.package for dep in deps]

    if dry_run:
        for repo in repos:
            click.echo(f"+ add-apt-repository -y {repo}")
        click.echo("+ apt-get update")
        click.echo(
            f"+ apt-get install -y --no-install-recommends {' '.join(packages)}"
        )
        click.echo("(dry-run — pass --yes to execute; BUILD-time / root only)")
        return 0

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        click.echo(
            "ERROR: install --yes needs root and runs at IMAGE-BUILD time only "
            "(agents are rootless --userns). Use it inside a container %post / "
            "Dockerfile, or pipe `dev system-deps list` into apt-get there.",
            err=True,
        )
        return 1

    for repo in repos:
        click.echo(f"+ add-apt-repository -y {repo}")
        if subprocess.run(["add-apt-repository", "-y", repo]).returncode != 0:
            click.echo(f"ERROR: add-apt-repository failed for {repo}", err=True)
            return 1
    if subprocess.run(["apt-get", "update"]).returncode != 0:
        click.echo("ERROR: apt-get update failed", err=True)
        return 1
    click.echo(f"+ apt-get install -y --no-install-recommends {' '.join(packages)}")
    rc = subprocess.run(
        ["apt-get", "install", "-y", "--no-install-recommends", *packages]
    ).returncode
    if rc != 0:
        click.echo("ERROR: apt-get install failed", err=True)
        return 1
    return 0


def register(group):
    @group.group("dev")
    def dev():
        """Developer / ecosystem utilities for scitex-audio."""

    @dev.group(
        "system-deps",
        invoke_without_command=True,
        epilog=(
            "Examples:\n"
            "  $ scitex-audio dev system-deps               # table\n"
            "  $ scitex-audio dev system-deps list          # apt names, one/line\n"
            "  $ apt-get install -y --no-install-recommends \\\n"
            "        $(scitex-audio dev system-deps list)\n"
            "  $ scitex-audio dev system-deps install       # BUILD-time, root\n"
            "\n"
            "Declared via the scitex_dev.system_deps entry point and federated by\n"
            "`scitex-dev ecosystem system-deps`. INSTALL IS BUILD-TIME ONLY\n"
            "(apt needs root; agents run rootless --userns)."
        ),
    )
    @click.pass_context
    def system_deps(ctx):
        """scitex-audio's declared system (apt) dependencies.

        With no subcommand, prints a human table; ``list`` is pipe-friendly;
        ``install`` applies them at image-build time.
        """
        if ctx.invoked_subcommand is None:
            _render(_declared())

    @system_deps.command(
        "list",
        epilog=(
            "Example:\n"
            "  $ scitex-audio dev system-deps list\n"
            "  $ apt-get install -y $(scitex-audio dev system-deps list)"
        ),
    )
    @click.option("--json", "as_json", is_flag=True, help="Emit structured JSON.")
    def system_deps_list(as_json):
        """Print scitex-audio's apt package names, one per line (pipe-friendly).

        \b
        Example:
            $ scitex-audio dev system-deps list
            $ apt-get install -y $(scitex-audio dev system-deps list)
        """
        deps = _declared()
        if as_json:
            _emit_json(deps)
            return 0
        for dep in deps:
            click.echo(dep.package)
        return 0

    @system_deps.command(
        "install",
        epilog=(
            "Example:\n"
            "  $ scitex-audio dev system-deps install        # preview\n"
            "  $ scitex-audio dev system-deps install --yes  # execute (root)"
        ),
    )
    @click.option(
        "--dry-run",
        is_flag=True,
        help="Print the apt commands without running them (default when --yes "
        "is omitted).",
    )
    @click.option(
        "--yes",
        "-y",
        "yes",
        is_flag=True,
        help="Actually run apt-get (BUILD-time; needs root).",
    )
    def system_deps_install(dry_run, yes):
        """apt-get install scitex-audio's set (BUILD-time; needs root).

        Mutating verb: previews (dry-run) unless --yes is given.

        \b
        Example:
            $ scitex-audio dev system-deps install        # preview
            $ scitex-audio dev system-deps install --yes  # execute (root)
        """
        return _do_install(_declared(), dry_run=dry_run or not yes)

    return dev


# EOF
