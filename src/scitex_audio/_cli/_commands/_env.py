#!/usr/bin/env python3
"""``show-env-template`` and ``list-python-apis`` commands for the CLI."""

import click


def register(group):
    @group.command("show-env-template")
    @click.option(
        "--output",
        "-o",
        type=click.Path(),
        help="Write template to file instead of stdout",
    )
    @click.option(
        "--no-sensitive",
        is_flag=True,
        help="Exclude sensitive variables (API keys)",
    )
    @click.option(
        "--json",
        "as_json",
        is_flag=True,
        help="Output as structured JSON (Result envelope).",
    )
    def env_template(output, no_sensitive, as_json):
        """
        Generate a template .src file for SCITEX_AUDIO_ENV_SRC

        \b
        Examples:
          scitex-audio show-env-template                    # Print to stdout
          scitex-audio show-env-template -o audio.src       # Write to file
          scitex-audio show-env-template --no-sensitive     # Exclude API keys
          scitex-audio show-env-template --json             # JSON envelope
        """
        from scitex_audio._env_registry import generate_template

        content = generate_template(include_sensitive=not no_sensitive)

        if as_json:
            from scitex_dev import Result

            click.echo(
                Result(
                    success=True,
                    data={
                        "template": content,
                        "include_sensitive": not no_sensitive,
                    },
                ).to_json()
            )
            return

        if output:
            from pathlib import Path

            Path(output).write_text(content + "\n")
            click.secho(f"Template written to {output}", fg="green")
            click.echo(f"  Usage: export SCITEX_AUDIO_ENV_SRC={output}")
        else:
            click.echo(content)

    @group.command("list-python-apis")
    @click.option(
        "-v", "--verbose", count=True, help="Verbosity: -v +doc, -vv full doc"
    )
    @click.option("-d", "--max-depth", type=int, default=5, help="Max recursion depth")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    @click.pass_context
    def list_python_apis(ctx, verbose, max_depth, as_json):
        """List Python APIs for scitex-audio.

        \b
        Example:
          $ scitex-audio list-python-apis
          $ scitex-audio list-python-apis -vv
          $ scitex-audio list-python-apis --json
        """
        try:
            from scitex.cli.introspect import api

            ctx.invoke(
                api,
                dotted_path="scitex_audio",
                verbose=verbose,
                max_depth=max_depth,
                as_json=as_json,
            )
        except ImportError:
            import inspect
            import json as json_mod

            import scitex_audio

            apis = []
            for name in scitex_audio.__all__:
                obj = getattr(scitex_audio, name, None)
                if obj is None:
                    continue
                entry = {"name": name, "type": type(obj).__name__}
                if verbose >= 1 and callable(obj):
                    try:
                        entry["signature"] = str(inspect.signature(obj))
                    except (ValueError, TypeError):
                        pass
                if verbose >= 2 and obj.__doc__:
                    entry["doc"] = obj.__doc__.strip().split("\n")[0]
                apis.append(entry)

            if as_json:
                click.echo(
                    json_mod.dumps(
                        {"success": True, "module": "scitex_audio", "apis": apis},
                        indent=2,
                    )
                )
            else:
                click.secho("scitex_audio Python APIs", fg="cyan", bold=True)
                click.echo("=" * 40)
                for a in apis:
                    name = click.style(a["name"], fg="green")
                    sig = a.get("signature", "")
                    click.echo(f"  {name}{sig}")
                    if "doc" in a:
                        click.echo(f"    {a['doc']}")

    return env_template, list_python_apis


# EOF
