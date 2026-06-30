"""Validate canonical and projected outputs."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from candidate_transformer.models import CanonicalProfile, OutputConfig


class ValidationFailure(ValueError):
    """Raised when output fails schema validation."""


def validate_canonical(profile: CanonicalProfile) -> CanonicalProfile:
    try:
        return CanonicalProfile.model_validate(profile.model_dump())
    except ValidationError as exc:
        raise ValidationFailure("Canonical profile validation failed") from exc


def validate_projected_output(output: dict[str, Any], config: OutputConfig | None) -> dict[str, Any]:
    if config is None or not config.fields:
        validate_canonical(CanonicalProfile.model_validate(output))
        return output

    for spec in config.fields:
        value = output.get(spec.path)
        if value is None and spec.required and config.on_missing == "error":
            raise ValidationFailure(f"Required projected field '{spec.path}' is missing")

        if value is None:
            continue

        if spec.type == "string" and not isinstance(value, str):
            raise ValidationFailure(f"Field '{spec.path}' must be string")
        if spec.type == "number" and not isinstance(value, (int, float)):
            raise ValidationFailure(f"Field '{spec.path}' must be number")
        if spec.type == "string[]" and not isinstance(value, list):
            raise ValidationFailure(f"Field '{spec.path}' must be string[]")
        if spec.type == "boolean" and not isinstance(value, bool):
            raise ValidationFailure(f"Field '{spec.path}' must be boolean")
        if spec.type == "object" and not isinstance(value, dict):
            raise ValidationFailure(f"Field '{spec.path}' must be object")

    return output
