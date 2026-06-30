"""Recruiter CSV structured source ingestor."""

from __future__ import annotations

import csv
from pathlib import Path

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import normalize_phone


def ingest_recruiter_csv(path: Path, source_id: str = "recruiter_csv") -> SourceRecord:
    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return SourceRecord(
                source_id=source_id,
                source_type="structured",
                fields=[],
                raw_confidence=0.0,
            )
        row = next(reader, None)
        if not row:
            return SourceRecord(
                source_id=source_id,
                source_type="structured",
                fields=[],
                raw_confidence=0.0,
            )

        name = (row.get("name") or row.get("full_name") or "").strip() or None
        email = (row.get("email") or "").strip().lower() or None
        phone_raw = (row.get("phone") or "").strip() or None
        company = (row.get("current_company") or row.get("company") or "").strip() or None
        title = (row.get("title") or row.get("current_title") or "").strip() or None
        location = (row.get("location") or "").strip() or None

        if name:
            fields.append(
                FieldValue(
                    field="full_name",
                    value=name,
                    source=source_id,
                    method="direct_map",
                    confidence=0.92,
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
                    method="direct_map",
                    confidence=0.95,
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
                    method="direct_map+normalize",
                    confidence=0.9,
                    structured=True,
                )
            )

        if title:
            fields.append(
                FieldValue(
                    field="headline",
                    value=title,
                    source=source_id,
                    method="direct_map",
                    confidence=0.85,
                    structured=True,
                )
            )

        if company and title:
            fields.append(
                FieldValue(
                    field="experience",
                    value=[{"company": company, "title": title, "start": None, "end": None, "summary": None}],
                    source=source_id,
                    method="direct_map",
                    confidence=0.88,
                    structured=True,
                )
            )

        if location:
            fields.append(
                FieldValue(
                    field="location",
                    value=location,
                    source=source_id,
                    method="direct_map",
                    confidence=0.8,
                    structured=True,
                )
            )

    return SourceRecord(
        source_id=source_id,
        source_type="structured",
        match_keys=match_keys,
        fields=fields,
        raw_confidence=0.9 if fields else 0.0,
    )
