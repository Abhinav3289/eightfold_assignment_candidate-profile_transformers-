"""Phone number normalization to E.164."""

from __future__ import annotations

import phonenumbers
from phonenumbers import NumberParseException


def normalize_phone(raw: str | None, default_region: str = "US") -> str | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    try:
        parsed = phonenumbers.parse(text, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) < 10:
            return None
        retry = f"+{digits}" if not text.startswith("+") else text
        try:
            parsed = phonenumbers.parse(retry, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            return None
    return None
