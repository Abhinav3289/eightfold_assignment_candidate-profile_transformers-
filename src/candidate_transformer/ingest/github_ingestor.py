"""GitHub profile unstructured source ingestor."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests

from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import canonicalize_skills


def _parse_github_username(value: str) -> str | None:
    text = value.strip()
    match = re.search(r"github\.com/([A-Za-z0-9-]+)", text)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9-]+", text):
        return text
    return None


def _fetch_github_user(username: str) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=8,
        )
        if response.status_code != 200:
            return None
        return response.json()
    except requests.RequestException:
        return None


def _fetch_top_languages(username: str) -> list[str]:
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": 10, "sort": "updated"},
            headers={"Accept": "application/vnd.github+json"},
            timeout=8,
        )
        if response.status_code != 200:
            return []
        repos = response.json()
        languages: set[str] = set()
        for repo in repos:
            if isinstance(repo, dict):
                lang = repo.get("language")
                if lang:
                    languages.add(str(lang))
        return sorted(languages)
    except requests.RequestException:
        return []


def _build_from_payload(data: dict[str, Any], source_id: str) -> SourceRecord:
    fields: list[FieldValue] = []
    match_keys: dict[str, str] = {}

    name = (data.get("name") or "").strip() or None
    bio = (data.get("bio") or "").strip() or None
    login = (data.get("login") or "").strip() or None
    html_url = (data.get("html_url") or "").strip() or None
    location = data.get("location")
    email = (data.get("email") or "").strip().lower() or None

    languages = data.get("languages") or data.get("top_languages") or []
    if isinstance(languages, dict):
        languages = list(languages.keys())

    if name:
        fields.append(
            FieldValue(
                field="full_name",
                value=name,
                source=source_id,
                method="github_api",
                confidence=0.72,
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
                method="github_api",
                confidence=0.7,
                structured=False,
            )
        )
        match_keys["email"] = email

    if bio:
        fields.append(
            FieldValue(
                field="headline",
                value=bio,
                source=source_id,
                method="github_api",
                confidence=0.68,
                structured=False,
            )
        )

    if location:
        fields.append(
            FieldValue(
                field="location",
                value=location,
                source=source_id,
                method="github_api",
                confidence=0.65,
                structured=False,
            )
        )

    if html_url or login:
        fields.append(
            FieldValue(
                field="links",
                value={
                    "linkedin": None,
                    "github": html_url or f"https://github.com/{login}",
                    "portfolio": data.get("blog") or None,
                    "other": [],
                },
                source=source_id,
                method="github_api",
                confidence=0.75,
                structured=False,
            )
        )

    if isinstance(languages, list) and languages:
        fields.append(
            FieldValue(
                field="skills",
                value=canonicalize_skills([str(x) for x in languages]),
                source=source_id,
                method="github_repos_languages",
                confidence=0.62,
                structured=False,
            )
        )

    return SourceRecord(
        source_id=source_id,
        source_type="unstructured",
        match_keys=match_keys,
        fields=fields,
        raw_confidence=0.7 if fields else 0.0,
    )


def ingest_github(path_or_url: Path | str, source_id: str = "github") -> SourceRecord:
    if isinstance(path_or_url, Path) and path_or_url.exists():
        with path_or_url.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)
        return _build_from_payload(data, source_id)

    username = _parse_github_username(str(path_or_url))
    if not username:
        return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)

    payload = _fetch_github_user(username)
    if not payload:
        return SourceRecord(source_id=source_id, source_type="unstructured", raw_confidence=0.0)

    languages = _fetch_top_languages(username)
    if languages:
        payload["top_languages"] = languages
    return _build_from_payload(payload, source_id)
