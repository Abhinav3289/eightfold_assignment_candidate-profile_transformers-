"""API service layer bridging HTTP uploads to the pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from candidate_transformer.models import OutputConfig
from candidate_transformer.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[3]
SAMPLES_DIR = ROOT / "data" / "samples"
EXAMPLE_CONFIG = ROOT / "config" / "custom_output.json"


def parse_output_config(raw: str | dict | None) -> OutputConfig | None:
    if raw is None:
        return None
    data = json.loads(raw) if isinstance(raw, str) else raw
    if not data:
        return None
    return OutputConfig.model_validate(data)


def load_example_config(
    include_provenance: bool = False,
    include_confidence: bool = True,
) -> OutputConfig:
    with EXAMPLE_CONFIG.open(encoding="utf-8") as handle:
        config = OutputConfig.model_validate(json.load(handle))
    config.include_provenance = include_provenance
    config.include_confidence = include_confidence
    return config


def build_default_config(
    include_provenance: bool = True,
    include_confidence: bool = True,
) -> OutputConfig:
    return OutputConfig(
        fields=[],
        include_provenance=include_provenance,
        include_confidence=include_confidence,
    )


def sample_input_paths() -> list[Path]:
    names = [
        "recruiter.csv",
        "ats.json",
        "github_profile.json",
        "resume.txt",
        "recruiter_notes.txt",
    ]
    return [SAMPLES_DIR / name for name in names if (SAMPLES_DIR / name).exists()]


def transform_uploaded_files(
    filenames_and_bytes: list[tuple[str, bytes]],
    output_config: OutputConfig | None = None,
) -> dict[str, Any]:
    if not filenames_and_bytes:
        raise ValueError("At least one input file is required")

    temp_dir = Path(tempfile.mkdtemp(prefix="candidate_api_"))
    input_paths: list[Path] = []
    try:
        for filename, content in filenames_and_bytes:
            safe_name = Path(filename).name
            if not safe_name:
                continue
            dest = temp_dir / safe_name
            dest.write_bytes(content)
            input_paths.append(dest)

        if not input_paths:
            raise ValueError("No valid input files were provided")

        return run_pipeline(input_paths, output_config)
    finally:
        for path in temp_dir.iterdir():
            path.unlink(missing_ok=True)
        temp_dir.rmdir()


def transform_samples(
    output_config: OutputConfig | None = None,
    use_custom_example: bool = False,
    include_provenance: bool = True,
    include_confidence: bool = True,
) -> dict[str, Any]:
    paths = sample_input_paths()
    if not paths:
        raise ValueError("Sample data is unavailable")

    if use_custom_example:
        config = load_example_config(include_provenance, include_confidence)
    elif output_config is not None:
        config = output_config
    else:
        config = build_default_config(include_provenance, include_confidence)

    return run_pipeline(paths, config)


def example_config_payload() -> dict[str, Any]:
    with EXAMPLE_CONFIG.open(encoding="utf-8") as handle:
        return json.load(handle)
