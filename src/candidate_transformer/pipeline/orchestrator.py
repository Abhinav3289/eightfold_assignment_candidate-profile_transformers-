"""End-to-end pipeline orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from candidate_transformer.confidence import score_profile
from candidate_transformer.ingest import (
    ingest_ats_json,
    ingest_github,
    ingest_recruiter_csv,
    ingest_recruiter_notes,
    ingest_resume,
)
from candidate_transformer.merge import merge_source_records
from candidate_transformer.models import OutputConfig, SourceRecord
from candidate_transformer.project import project_profile
from candidate_transformer.validate import validate_canonical, validate_projected_output


def _detect_and_ingest(path: Path) -> SourceRecord | None:
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix == ".csv":
        return ingest_recruiter_csv(path, source_id=path.stem)
    if suffix == ".json" and "github" in name:
        return ingest_github(path, source_id=path.stem)
    if suffix == ".json":
        return ingest_ats_json(path, source_id=path.stem)
    if suffix in {".txt", ".pdf", ".docx", ".doc"} and "note" in name:
        return ingest_recruiter_notes(path, source_id=path.stem)
    if suffix in {".txt", ".pdf", ".docx", ".doc"}:
        return ingest_resume(path, source_id=path.stem)
    if "github.com" in str(path):
        return ingest_github(str(path), source_id="github_live")
    return None


def run_pipeline(
    input_paths: list[Path] | None = None,
    output_config: OutputConfig | None = None,
    source_records: list[SourceRecord] | None = None,
) -> dict[str, Any]:
    records: list[SourceRecord] = []
    for path in input_paths or []:
        record = _detect_and_ingest(path)
        if record and record.fields:
            records.append(record)

    for record in source_records or []:
        if record.fields:
            records.append(record)

    if not records:
        raise ValueError("No valid source records were extracted from the provided inputs")

    profile = merge_source_records(records)
    profile.overall_confidence = score_profile(profile)
    profile = validate_canonical(profile)

    projected = project_profile(profile, output_config)
    return validate_projected_output(projected, output_config)


def load_output_config(config_path: Path | None) -> OutputConfig | None:
    if config_path is None:
        return None
    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return OutputConfig.model_validate(data)
