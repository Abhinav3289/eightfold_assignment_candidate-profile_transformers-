"""Date normalization to YYYY-MM."""

from __future__ import annotations

import re
from datetime import datetime

from dateutil import parser as date_parser

_MONTHS = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def normalize_date(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip().lower()
    if text in {"present", "current", "now", "ongoing"}:
        return None

    if re.fullmatch(r"\d{4}-\d{2}", text):
        return text
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01"

    month_year = re.match(r"([a-z]{3,9})\s+(\d{4})", text)
    if month_year:
        month_key = month_year.group(1)[:3]
        year = month_year.group(2)
        month = _MONTHS.get(month_key)
        if month:
            return f"{year}-{month}"

    try:
        parsed = date_parser.parse(text, default=datetime(2000, 1, 1))
        return parsed.strftime("%Y-%m")
    except (ValueError, OverflowError, TypeError):
        return None
