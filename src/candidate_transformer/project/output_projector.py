"""Project canonical profile to configurable output schema."""

from __future__ import annotations

from typing import Any

from candidate_transformer.extract import get_by_path
from candidate_transformer.models import CanonicalProfile, OutputConfig, OutputFieldSpec
from candidate_transformer.normalize import canonicalize_skills, normalize_phone


class ProjectionError(ValueError):
    """Raised when required projected fields are missing."""


def _apply_normalize(value: Any, rule: str | None) -> Any:
    if value is None or rule in (None, "none"):
        return value
    if rule == "E164":
        if isinstance(value, list):
            return [normalize_phone(str(v)) for v in value if normalize_phone(str(v))]
        return normalize_phone(str(value))
    if rule == "canonical":
        if isinstance(value, list):
            return canonicalize_skills([str(v) for v in value])
        return canonicalize_skills([str(value)])[0] if value else None
    return value


def _coerce_type(value: Any, field_type: str) -> Any:
    if value is None:
        return None
    if field_type == "string":
        if isinstance(value, list):
            return str(value[0]) if value else None
        return str(value)
    if field_type == "number":
        return float(value)
    if field_type == "string[]":
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]
    if field_type == "boolean":
        return bool(value)
    if field_type == "object":
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value
    return value


def _resolve_field(profile: CanonicalProfile, spec: OutputFieldSpec) -> Any:
    source_path = spec.from_ or spec.path
    profile_dict = profile.model_dump()
    value = get_by_path(profile_dict, source_path)
    value = _apply_normalize(value, spec.normalize)
    return _coerce_type(value, spec.type)


def project_profile(profile: CanonicalProfile, config: OutputConfig | None) -> dict[str, Any]:
    if config is None or not config.fields:
        output = profile.model_dump()
        if not config or config.include_provenance:
            pass
        else:
            output.pop("provenance", None)
        if config and not config.include_confidence:
            output.pop("overall_confidence", None)
        return output

    result: dict[str, Any] = {}
    for spec in config.fields:
        value = _resolve_field(profile, spec)
        if value is None:
            if spec.required and config.on_missing == "error":
                raise ProjectionError(f"Required field '{spec.path}' is missing")
            if config.on_missing == "omit":
                continue
            value = None
        result[spec.path] = value

    if config.include_confidence:
        result["overall_confidence"] = profile.overall_confidence
    if config.include_provenance:
        result["provenance"] = [entry.model_dump() for entry in profile.provenance]
    return result
