"""Manual form input ingestor for UI-driven testing."""

from __future__ import annotations

from typing import Any

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import (
    canonicalize_skills,
    normalize_country,
    normalize_date,
    normalize_phone,
)


def _split_csv(value: str | None) -> list[str]:
    if not value or not str(value).strip():
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def ingest_manual_form(
    data: dict[str, Any],
    source_id: str = "manual_ui",
    structured: bool = True,
) -> SourceRecord:
    """Convert manually entered UI fields into a SourceRecord."""
    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}
    source_type = "structured" if structured else "unstructured"
    base_confidence = 0.85 if structured else 0.65

    full_name = (data.get("full_name") or "").strip() or None
    email = (data.get("email") or "").strip().lower() or None
    phone = normalize_phone((data.get("phone") or "").strip() or None)
    headline = (data.get("headline") or "").strip() or None
    years_raw = data.get("years_experience")

    city = (data.get("city") or "").strip() or None
    region = (data.get("region") or "").strip() or None
    country = normalize_country((data.get("country") or "").strip() or None)

    linkedin = (data.get("linkedin") or "").strip() or None
    github = (data.get("github") or "").strip() or None
    portfolio = (data.get("portfolio") or "").strip() or None

    skills = canonicalize_skills(_split_csv(data.get("skills")))

    company = (data.get("company") or "").strip() or None
    title = (data.get("title") or "").strip() or None
    start = normalize_date((data.get("start_date") or "").strip() or None)
    end = normalize_date((data.get("end_date") or "").strip() or None)
    summary = (data.get("summary") or "").strip() or None

    institution = (data.get("institution") or "").strip() or None
    degree = (data.get("degree") or "").strip() or None
    field = (data.get("field") or "").strip() or None
    end_year_raw = data.get("end_year")
    end_year: int | None = None
    if end_year_raw not in (None, ""):
        try:
            end_year = int(str(end_year_raw)[:4])
        except ValueError:
            end_year = None

    notes = (data.get("notes") or "").strip() or None

    if full_name:
        fields.append(
            FieldValue(
                field="full_name",
                value=full_name,
                source=source_id,
                method="manual_form",
                confidence=base_confidence,
                structured=structured,
            )
        )
        match_keys["name"] = full_name.lower()

    if email:
        fields.append(
            FieldValue(
                field="emails",
                value=[email],
                source=source_id,
                method="manual_form",
                confidence=base_confidence,
                structured=structured,
            )
        )
        match_keys["email"] = email

    if phone:
        fields.append(
            FieldValue(
                field="phones",
                value=[phone],
                source=source_id,
                method="manual_form+normalize",
                confidence=base_confidence - 0.05,
                structured=structured,
            )
        )

    if headline:
        fields.append(
            FieldValue(
                field="headline",
                value=headline,
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.05,
                structured=structured,
            )
        )

    if city or region or country:
        fields.append(
            FieldValue(
                field="location",
                value={"city": city, "region": region, "country": country},
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.1,
                structured=structured,
            )
        )

    if years_raw not in (None, ""):
        try:
            years = float(years_raw)
            fields.append(
                FieldValue(
                    field="years_experience",
                    value=years,
                    source=source_id,
                    method="manual_form",
                    confidence=base_confidence - 0.15,
                    structured=structured,
                )
            )
        except (TypeError, ValueError):
            pass

    if linkedin or github or portfolio:
        fields.append(
            FieldValue(
                field="links",
                value={
                    "linkedin": linkedin,
                    "github": github,
                    "portfolio": portfolio,
                    "other": [],
                },
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.1,
                structured=structured,
            )
        )

    if skills:
        fields.append(
            FieldValue(
                field="skills",
                value=skills,
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.1,
                structured=structured,
            )
        )

    if company or title:
        fields.append(
            FieldValue(
                field="experience",
                value=[
                    {
                        "company": company,
                        "title": title,
                        "start": start,
                        "end": end,
                        "summary": summary,
                    }
                ],
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.08,
                structured=structured,
            )
        )

    if institution or degree:
        fields.append(
            FieldValue(
                field="education",
                value=[
                    {
                        "institution": institution,
                        "degree": degree,
                        "field": field,
                        "end_year": end_year,
                    }
                ],
                source=source_id,
                method="manual_form",
                confidence=base_confidence - 0.08,
                structured=structured,
            )
        )

    if notes:
        fields.append(
            FieldValue(
                field="headline",
                value=notes[:120],
                source=source_id,
                method="manual_notes",
                confidence=0.5,
                structured=False,
            )
        )
        note_skills = canonicalize_skills(_split_csv(data.get("note_skills")))
        if note_skills:
            fields.append(
                FieldValue(
                    field="skills",
                    value=note_skills,
                    source=source_id,
                    method="manual_notes",
                    confidence=0.48,
                    structured=False,
                )
            )

    return SourceRecord(
        source_id=source_id,
        source_type=source_type,
        match_keys=match_keys,
        fields=fields,
        raw_confidence=base_confidence if fields else 0.0,
    )
