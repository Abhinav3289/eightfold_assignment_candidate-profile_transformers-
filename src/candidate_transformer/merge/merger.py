"""Merge multiple source records into one canonical profile."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from candidate_transformer.models import (
    CanonicalProfile,
    EducationEntry,
    ExperienceEntry,
    FieldValue,
    Links,
    Location,
    ProvenanceEntry,
    SkillEntry,
    SourceRecord,
)
from candidate_transformer.normalize import canonicalize_skill, canonicalize_skills, normalize_location, normalize_phone


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _merge_scalar(
    candidates: list[FieldValue],
) -> tuple[Any, ProvenanceEntry | None]:
    if not candidates:
        return None, None
    ranked = sorted(
        candidates,
        key=lambda item: (item.structured, item.confidence),
        reverse=True,
    )
    winner = ranked[0]
    return winner.value, ProvenanceEntry(
        field=winner.field,
        source=winner.source,
        method=winner.method,
        confidence=winner.confidence,
    )


def _merge_list_field(
    field: str,
    candidates: list[FieldValue],
) -> tuple[list[Any], list[ProvenanceEntry]]:
    if not candidates:
        return [], []
    merged: list[Any] = []
    provenance: list[ProvenanceEntry] = []
    for candidate in sorted(candidates, key=lambda x: x.confidence, reverse=True):
        values = candidate.value if isinstance(candidate.value, list) else [candidate.value]
        for value in values:
            if value is None:
                continue
            if value not in merged:
                merged.append(value)
                provenance.append(
                    ProvenanceEntry(
                        field=field,
                        source=candidate.source,
                        method=candidate.method,
                        confidence=candidate.confidence,
                    )
                )
    return merged, provenance


def _merge_skills(candidates: list[FieldValue]) -> tuple[list[SkillEntry], list[ProvenanceEntry]]:
    skill_map: dict[str, SkillEntry] = {}
    provenance: list[ProvenanceEntry] = []
    for candidate in candidates:
        raw_values = candidate.value if isinstance(candidate.value, list) else [candidate.value]
        for raw in raw_values:
            canonical = canonicalize_skill(str(raw))
            if not canonical:
                continue
            existing = skill_map.get(canonical)
            if existing is None or candidate.confidence > existing.confidence:
                skill_map[canonical] = SkillEntry(
                    name=canonical,
                    confidence=candidate.confidence,
                    sources=[candidate.source],
                )
                provenance.append(
                    ProvenanceEntry(
                        field="skills",
                        source=candidate.source,
                        method=candidate.method,
                        confidence=candidate.confidence,
                    )
                )
            elif candidate.source not in existing.sources:
                existing.sources.append(candidate.source)
    return list(skill_map.values()), provenance


def _merge_experience(candidates: list[FieldValue]) -> tuple[list[ExperienceEntry], list[ProvenanceEntry]]:
    entry_map: dict[tuple[str, str], ExperienceEntry] = {}
    provenance: list[ProvenanceEntry] = []
    for candidate in sorted(candidates, key=lambda x: (x.structured, x.confidence), reverse=True):
        raw_entries = candidate.value if isinstance(candidate.value, list) else []
        for raw in raw_entries:
            if not isinstance(raw, dict):
                continue
            company = (raw.get("company") or "").strip()
            title = (raw.get("title") or "").strip()
            key = (company.lower(), title.lower())
            if not company and not title:
                continue
            existing = entry_map.get(key)
            incoming = ExperienceEntry(**raw)
            if existing is None:
                entry_map[key] = incoming
                provenance.append(
                    ProvenanceEntry(
                        field="experience",
                        source=candidate.source,
                        method=candidate.method,
                        confidence=candidate.confidence,
                    )
                )
                continue
            if existing.start is None and incoming.start:
                existing.start = incoming.start
            if existing.end is None and incoming.end:
                existing.end = incoming.end
            if existing.summary is None and incoming.summary:
                existing.summary = incoming.summary
    return list(entry_map.values()), provenance


def _merge_education(candidates: list[FieldValue]) -> tuple[list[EducationEntry], list[ProvenanceEntry]]:
    entry_map: dict[tuple[str, str], EducationEntry] = {}
    provenance: list[ProvenanceEntry] = []
    for candidate in sorted(candidates, key=lambda x: (x.structured, x.confidence), reverse=True):
        raw_entries = candidate.value if isinstance(candidate.value, list) else []
        for raw in raw_entries:
            if not isinstance(raw, dict):
                continue
            institution = re.sub(r"\s*\(\d{4}\)\s*$", "", (raw.get("institution") or "").strip())
            degree = (raw.get("degree") or "").strip()
            key = (institution.lower(), degree.lower())
            if not institution:
                continue
            incoming = EducationEntry(
                institution=institution,
                degree=degree or None,
                field=raw.get("field"),
                end_year=raw.get("end_year"),
            )
            existing = entry_map.get(key)
            if existing is None:
                entry_map[key] = incoming
                provenance.append(
                    ProvenanceEntry(
                        field="education",
                        source=candidate.source,
                        method=candidate.method,
                        confidence=candidate.confidence,
                    )
                )
                continue
            if existing.field is None and incoming.field:
                existing.field = incoming.field
            if existing.end_year is None and incoming.end_year:
                existing.end_year = incoming.end_year
    return list(entry_map.values()), provenance


def _merge_links(candidates: list[FieldValue]) -> tuple[Links, list[ProvenanceEntry]]:
    links = Links()
    provenance: list[ProvenanceEntry] = []
    for candidate in sorted(candidates, key=lambda x: (x.structured, x.confidence), reverse=True):
        if not isinstance(candidate.value, dict):
            continue
        for key in ("linkedin", "github", "portfolio"):
            value = candidate.value.get(key)
            if value and getattr(links, key) is None:
                setattr(links, key, value)
                provenance.append(
                    ProvenanceEntry(
                        field=f"links.{key}",
                        source=candidate.source,
                        method=candidate.method,
                        confidence=candidate.confidence,
                    )
                )
        other = candidate.value.get("other") or []
        for item in other:
            if item and item not in links.other:
                links.other.append(item)
    return links, provenance


def _derive_candidate_id(records: list[SourceRecord]) -> str:
    for record in records:
        email = record.match_keys.get("email")
        if email:
            digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]
            return f"cand_{digest}"
    for record in records:
        name = record.match_keys.get("name")
        if name:
            digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
            return f"cand_{digest}"
    digest = hashlib.sha256(str(len(records)).encode("utf-8")).hexdigest()[:12]
    return f"cand_{digest}"


def records_match(record_a: SourceRecord, record_b: SourceRecord) -> bool:
    email_a = record_a.match_keys.get("email")
    email_b = record_b.match_keys.get("email")
    if email_a and email_b and email_a == email_b:
        return True
    name_a = record_a.match_keys.get("name")
    name_b = record_b.match_keys.get("name")
    if name_a and name_b:
        norm_a = re.sub(r"[^a-z]", "", name_a.lower())
        norm_b = re.sub(r"[^a-z]", "", name_b.lower())
        return norm_a == norm_b
    return False


def merge_source_records(records: list[SourceRecord]) -> CanonicalProfile:
    grouped: dict[str, list[FieldValue]] = {}
    for record in records:
        for field in record.fields:
            grouped.setdefault(field.field, []).append(field)

    provenance: list[ProvenanceEntry] = []

    full_name, name_prov = _merge_scalar(grouped.get("full_name", []))
    if name_prov:
        provenance.append(name_prov)

    emails_raw, email_prov = _merge_list_field("emails", grouped.get("emails", []))
    emails = _dedupe_strings([str(e).lower() for e in emails_raw if e])
    provenance.extend(email_prov)

    phones_raw, phone_prov = _merge_list_field("phones", grouped.get("phones", []))
    phones = []
    for raw in phones_raw:
        normalized = normalize_phone(str(raw))
        if normalized:
            phones.append(normalized)
    phones = _dedupe_strings(phones)
    provenance.extend(phone_prov)

    location_candidates = grouped.get("location", [])
    location_value = None
    location_prov = None
    if location_candidates:
        location_value, location_prov = _merge_scalar(location_candidates)
    location_dict = normalize_location(location_value)
    location = Location(**location_dict)
    if location_prov:
        provenance.append(location_prov)

    headline, headline_prov = _merge_scalar(grouped.get("headline", []))
    if headline_prov:
        provenance.append(headline_prov)

    years_experience, years_prov = _merge_scalar(grouped.get("years_experience", []))
    if years_prov:
        provenance.append(years_prov)

    skills, skills_prov = _merge_skills(grouped.get("skills", []))
    provenance.extend(skills_prov)

    experience, exp_prov = _merge_experience(grouped.get("experience", []))
    provenance.extend(exp_prov)

    education, edu_prov = _merge_education(grouped.get("education", []))
    provenance.extend(edu_prov)

    links, links_prov = _merge_links(grouped.get("links", []))
    provenance.extend(links_prov)

    candidate_id = _derive_candidate_id(records)

    return CanonicalProfile(
        candidate_id=candidate_id,
        full_name=full_name,
        emails=emails,
        phones=phones,
        location=location,
        links=links,
        headline=headline,
        years_experience=float(years_experience) if years_experience is not None else None,
        skills=skills,
        experience=experience,
        education=education,
        provenance=provenance,
    )
