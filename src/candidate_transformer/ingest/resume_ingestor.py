"""Resume file unstructured source ingestor (TXT, PDF, DOCX)."""

from __future__ import annotations

import re
from pathlib import Path

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import canonicalize_skills, normalize_date, normalize_phone


def _read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in {".docx", ".doc"}:
        from docx import Document

        document = Document(str(path))
        return "\n".join(p.text for p in document.paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_email(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0).lower() if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(\+?\d[\d\s().-]{8,}\d)", text)
    if not match:
        return None
    return normalize_phone(match.group(1))


def _extract_name(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    candidate = lines[0]
    if "@" in candidate or len(candidate) > 60:
        return None
    if re.fullmatch(r"[A-Za-z .'-]{3,60}", candidate):
        return candidate
    return None


def _extract_skills(text: str) -> list[str]:
    section_match = re.search(
        r"(?is)(skills|technical skills|technologies)\s*[:\-]?\s*(.+?)(?:\n\s*\n|experience|education|$)",
        text,
    )
    if not section_match:
        return []
    chunk = section_match.group(2)
    tokens = re.split(r"[,|/\n•\-]+", chunk)
    return canonicalize_skills([t.strip() for t in tokens if t.strip()])


def _section_text(text: str, section_name: str) -> str:
    pattern = rf"(?is){section_name}\s*\n(.+?)(?:\n\s*\n[A-Za-z][A-Za-z ]{{2,}}\n|$)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _extract_experience(text: str) -> list[dict]:
    entries: list[dict] = []
    section = _section_text(text, "experience")
    if not section:
        return entries
    pattern = re.compile(
        r"(?m)^(?P<title>[A-Za-z0-9 /&.-]{3,80})\s*[-@|]\s*(?P<company>[A-Za-z0-9 &.,'-]{2,80})"
        r"(?:\s*\((?P<dates>[^)]+)\))?"
    )
    for match in pattern.finditer(section):
        title = match.group("title").strip()
        company = match.group("company").strip()
        if "@" in title or "@" in company or "." in title:
            continue
        dates = match.group("dates") or ""
        start, end = None, None
        if dates:
            parts = re.split(r"\s*[-–—to]+\s*", dates)
            if parts:
                start = normalize_date(parts[0])
            if len(parts) > 1:
                end = normalize_date(parts[1])
        entries.append(
            {
                "company": company,
                "title": title,
                "start": start,
                "end": end,
                "summary": None,
            }
        )
    return entries[:5]


def _extract_education(text: str) -> list[dict]:
    entries: list[dict] = []
    section = _section_text(text, "education")
    if not section:
        return entries
    pattern = re.compile(
        r"(?m)^(?P<degree>B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|[A-Za-z .'-]{3,40})\s*[-,]\s*"
        r"(?P<institution>[A-Za-z0-9 .,'&()-]{3,80})(?:\s*\((?P<year>\d{4})\))?"
    )
    for match in pattern.finditer(section):
        year = match.group("year")
        entries.append(
            {
                "institution": match.group("institution").strip(),
                "degree": match.group("degree").strip(),
                "field": None,
                "end_year": int(year) if year else None,
            }
        )
    return entries[:3]


def ingest_resume(path: Path, source_id: str = "resume") -> SourceRecord:
    if not path.exists():
        return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)

    try:
        text = _read_text(path)
    except Exception:
        return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)

    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}

    name = _extract_name(text)
    email = _extract_email(text)
    phone = _extract_phone(text)
    skills = _extract_skills(text)
    experience = _extract_experience(text)
    education = _extract_education(text)

    if name:
        fields.append(
            FieldValue(
                field="full_name",
                value=name,
                source=source_id,
                method="resume_heuristic",
                confidence=0.62,
                structured=False,
            )
        )
        match_keys["name"] = name.lower()

    if email:
        fields.append(
            FieldValue(
                field="emails",
                value=[email],
                source=source_id,
                method="regex",
                confidence=0.66,
                structured=False,
            )
        )
        match_keys["email"] = email

    if phone:
        fields.append(
            FieldValue(
                field="phones",
                value=[phone],
                source=source_id,
                method="regex+normalize",
                confidence=0.6,
                structured=False,
            )
        )

    if skills:
        fields.append(
            FieldValue(
                field="skills",
                value=skills,
                source=source_id,
                method="section_parse",
                confidence=0.58,
                structured=False,
            )
        )

    if experience:
        fields.append(
            FieldValue(
                field="experience",
                value=experience,
                source=source_id,
                method="section_parse",
                confidence=0.55,
                structured=False,
            )
        )

    if education:
        fields.append(
            FieldValue(
                field="education",
                value=education,
                source=source_id,
                method="section_parse",
                confidence=0.55,
                structured=False,
            )
        )

    return SourceRecord(
        source_id=source_id,
        source_type="unstructured",
        match_keys=match_keys,
        fields=fields,
        raw_confidence=0.6 if fields else 0.0,
    )
