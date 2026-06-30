"""Recruiter free-form notes unstructured source ingestor."""

from __future__ import annotations

import re
from pathlib import Path

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import canonicalize_skills


def ingest_recruiter_notes(path: Path, source_id: str = "recruiter_notes") -> SourceRecord:
    if not path.exists():
        return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)

    text = path.read_text(encoding="utf-8", errors="ignore")
    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if email_match:
        email = email_match.group(0).lower()
        fields.append(
            FieldValue(
                field="emails",
                value=[email],
                source=source_id,
                method="notes_regex",
                confidence=0.5,
                structured=False,
            )
        )
        match_keys["email"] = email

    years_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?(?:\s+of)?\s+experience", text, re.I)
    if years_match:
        fields.append(
            FieldValue(
                field="years_experience",
                value=float(years_match.group(1)),
                source=source_id,
                method="notes_regex",
                confidence=0.48,
                structured=False,
            )
        )

    headline_match = re.search(r"(?:strong|excellent|solid)\s+([A-Za-z .+/]+?)\s+(?:engineer|developer|candidate)", text, re.I)
    if headline_match:
        fields.append(
            FieldValue(
                field="headline",
                value=headline_match.group(0).strip().capitalize(),
                source=source_id,
                method="notes_heuristic",
                confidence=0.45,
                structured=False,
            )
        )

    skill_tokens = re.findall(r"\b(Python|Java|JavaScript|TypeScript|React|AWS|Docker|Kubernetes|SQL|Go|Rust)\b", text, re.I)
    if skill_tokens:
        fields.append(
            FieldValue(
                field="skills",
                value=canonicalize_skills(skill_tokens),
                source=source_id,
                method="notes_keyword",
                confidence=0.46,
                structured=False,
            )
        )

    linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+", text)
    if linkedin_match:
        fields.append(
            FieldValue(
                field="links",
                value={"linkedin": linkedin_match.group(0), "github": None, "portfolio": None, "other": []},
                source=source_id,
                method="notes_regex",
                confidence=0.52,
                structured=False,
            )
        )

    return SourceRecord(
        source_id=source_id,
        source_type="unstructured",
        match_keys=match_keys,
        fields=fields,
        raw_confidence=0.5 if fields else 0.0,
    )
