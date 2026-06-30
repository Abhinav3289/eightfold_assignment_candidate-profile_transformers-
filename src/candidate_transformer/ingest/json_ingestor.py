"""ATS JSON semi-structured source ingestor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import normalize_date, normalize_phone


def _first_str(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _extract_experience(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("work_history") or data.get("employment") or data.get("experience") or []
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        entries.append(
            {
                "company": _first_str(item, "employer", "company", "organization"),
                "title": _first_str(item, "role", "title", "position"),
                "start": normalize_date(_first_str(item, "start_date", "start", "from")),
                "end": normalize_date(_first_str(item, "end_date", "end", "to")),
                "summary": _first_str(item, "description", "summary"),
            }
        )
    return entries


def _extract_education(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("education_history") or data.get("education") or []
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        end_year_raw = item.get("graduation_year") or item.get("end_year") or item.get("year")
        end_year: int | None = None
        if end_year_raw is not None:
            try:
                end_year = int(str(end_year_raw)[:4])
            except ValueError:
                end_year = None
        entries.append(
            {
                "institution": _first_str(item, "school", "institution", "university"),
                "degree": _first_str(item, "degree", "qualification"),
                "field": _first_str(item, "major", "field", "discipline"),
                "end_year": end_year,
            }
        )
    return entries


def ingest_ats_json(path: Path, source_id: str = "ats_json") -> SourceRecord:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return SourceRecord(source_id=source_id, source_type="structured", raw_confidence=0.0)

    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}

    name = _first_str(data, "candidate_name", "fullName", "name")
    email = _first_str(data, "contact_email", "email", "primaryEmail")
    if email:
        email = email.lower()
    phone_raw = _first_str(data, "mobile", "phone", "contact_phone")
    headline = _first_str(data, "current_role", "headline", "job_title")
    location = data.get("location") or data.get("address")
    skills_raw = data.get("skill_tags") or data.get("skills") or []
    years = data.get("total_experience_years") or data.get("years_experience")

    if name:
        fields.append(
            FieldValue(
                field="full_name",
                value=name,
                source=source_id,
                method="schema_map",
                confidence=0.88,
                structured=True,
            )
        )
        match_keys["name"] = name.lower()

    if email:
        fields.append(
            FieldValue(
                field="emails",
                value=[email],
                source=source_id,
                method="schema_map",
                confidence=0.9,
                structured=True,
            )
        )
        match_keys["email"] = email

    phone = normalize_phone(phone_raw)
    if phone:
        fields.append(
            FieldValue(
                field="phones",
                value=[phone],
                source=source_id,
                method="schema_map+normalize",
                confidence=0.85,
                structured=True,
            )
        )

    if headline:
        fields.append(
            FieldValue(
                field="headline",
                value=headline,
                source=source_id,
                method="schema_map",
                confidence=0.82,
                structured=True,
            )
        )

    if location:
        fields.append(
            FieldValue(
                field="location",
                value=location,
                source=source_id,
                method="schema_map",
                confidence=0.78,
                structured=True,
            )
        )

    if isinstance(skills_raw, list) and skills_raw:
        skills = [str(s).strip() for s in skills_raw if str(s).strip()]
        fields.append(
            FieldValue(
                field="skills",
                value=skills,
                source=source_id,
                method="schema_map",
                confidence=0.8,
                structured=True,
            )
        )

    experience = _extract_experience(data)
    if experience:
        fields.append(
            FieldValue(
                field="experience",
                value=experience,
                source=source_id,
                method="schema_map",
                confidence=0.86,
                structured=True,
            )
        )

    education = _extract_education(data)
    if education:
        fields.append(
            FieldValue(
                field="education",
                value=education,
                source=source_id,
                method="schema_map",
                confidence=0.84,
                structured=True,
            )
        )

    if years is not None:
        try:
            years_val = float(years)
            fields.append(
                FieldValue(
                    field="years_experience",
                    value=years_val,
                    source=source_id,
                    method="schema_map",
                    confidence=0.75,
                    structured=True,
                )
            )
        except (TypeError, ValueError):
            pass

    linkedin = _first_str(data, "linkedin_url", "linkedin")
    github = _first_str(data, "github_url", "github")
    if linkedin or github:
        fields.append(
            FieldValue(
                field="links",
                value={"linkedin": linkedin, "github": github, "portfolio": None, "other": []},
                source=source_id,
                method="schema_map",
                confidence=0.8,
                structured=True,
            )
        )

    return SourceRecord(
        source_id=source_id,
        source_type="structured",
        match_keys=match_keys,
        fields=fields,
        raw_confidence=0.85 if fields else 0.0,
    )
