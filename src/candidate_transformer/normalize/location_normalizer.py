"""Location normalization with ISO-3166 alpha-2 country codes."""

from __future__ import annotations

COUNTRY_ALIASES: dict[str, str] = {
    "usa": "US",
    "us": "US",
    "united states": "US",
    "united states of america": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "england": "GB",
    "india": "IN",
    "in": "IN",
    "canada": "CA",
    "ca": "CA",
    "germany": "DE",
    "de": "DE",
    "australia": "AU",
    "au": "AU",
    "singapore": "SG",
    "sg": "SG",
}


def normalize_country(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    if len(text) == 2 and text.isalpha():
        return text.upper()
    mapped = COUNTRY_ALIASES.get(text.lower())
    return mapped


def normalize_location(raw: str | dict | None) -> dict[str, str | None]:
    if raw is None:
        return {"city": None, "region": None, "country": None}
    if isinstance(raw, dict):
        return {
            "city": raw.get("city") or raw.get("locality"),
            "region": raw.get("region") or raw.get("state") or raw.get("province"),
            "country": normalize_country(raw.get("country")),
        }

    text = str(raw).strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 3:
        return {
            "city": parts[0],
            "region": parts[1],
            "country": normalize_country(parts[2]),
        }
    if len(parts) == 2:
        return {
            "city": parts[0],
            "region": None,
            "country": normalize_country(parts[1]),
        }
    return {"city": parts[0] if parts else None, "region": None, "country": None}
