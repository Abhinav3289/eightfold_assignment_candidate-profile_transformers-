"""Command-line interface for the candidate transformer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from candidate_transformer.pipeline import load_output_config, run_pipeline

app = typer.Typer(
    name="candidate-transformer",
    help="Multi-source candidate data transformer with configurable output projection.",
    add_completion=False,
)


@app.command()
def transform(
    inputs: list[Path] = typer.Argument(..., help="Input source files (CSV, JSON, resume, notes, GitHub JSON)."),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Optional output projection config JSON.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write JSON result to this file instead of stdout.",
    ),
    pretty: bool = typer.Option(True, "--pretty/--compact", help="Pretty-print JSON output."),
) -> None:
    """Run detect -> ingest -> normalize -> merge -> confidence -> project -> validate."""
    missing = [str(path) for path in inputs if not path.exists()]
    if missing:
        typer.secho(f"Input file(s) not found: {', '.join(missing)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        output_config = load_output_config(config)
        result = run_pipeline(inputs, output_config)
    except Exception as exc:
        typer.secho(f"Pipeline failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    indent = 2 if pretty else None
    payload = json.dumps(result, indent=indent, ensure_ascii=False)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
        typer.secho(f"Wrote output to {output}", fg=typer.colors.GREEN)
    else:
        typer.echo(payload)


if __name__ == "__main__":
    app()
