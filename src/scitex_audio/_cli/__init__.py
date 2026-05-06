#!/usr/bin/env python3
"""SciTeX Audio CLI."""

import json
import sys

import click

from ._main import audio as main

__all__ = ["main", "print_help_recursive", "group_to_json"]


def print_help_recursive(ctx, group, prefix=""):
    """Print help for a click group and all its subcommands recursively."""
    click.echo(group.get_help(ctx))
    click.echo()

    commands = getattr(group, "commands", {})
    for name in sorted(commands):
        cmd = commands[name]
        sub_ctx = click.Context(cmd, info_name=name, parent=ctx)
        if isinstance(cmd, click.Group):
            click.echo(f"{'=' * 60}")
            click.echo(f"Subgroup: {prefix}{name}")
            click.echo(f"{'=' * 60}")
            print_help_recursive(sub_ctx, cmd, prefix=f"{prefix}{name} ")
        else:
            click.echo(f"--- {prefix}{name} ---")
            click.echo(cmd.get_help(sub_ctx))
            click.echo()


def group_to_json(ctx, group):
    """Output a click group's commands as JSON."""
    try:
        from scitex_dev import Result
    except ImportError:
        # Fallback without scitex_dev
        commands = {}
        for name in sorted(getattr(group, "commands", {})):
            cmd = group.commands[name]
            commands[name] = {
                "name": name,
                "help": cmd.get_short_help_str(limit=200),
            }
        click.echo(json.dumps({"success": True, "commands": commands}, indent=2))
        return

    commands = {}
    for name in sorted(getattr(group, "commands", {})):
        cmd = group.commands[name]
        commands[name] = {
            "name": name,
            "help": cmd.get_short_help_str(limit=200),
        }
    click.echo(Result(success=True, data={"commands": commands}).to_json())


# audit §4 — inject version into root --help
try:
    from importlib.metadata import version as _v
    main.help = (
        f"scitex-audio (v{_v('scitex-audio')}) — "
        + (main.help or "").lstrip()
    )
except Exception:
    pass
