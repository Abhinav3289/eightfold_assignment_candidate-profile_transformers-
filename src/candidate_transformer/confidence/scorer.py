"""Overall confidence scoring for canonical profiles."""

from __future__ import annotations

from candidate_transformer.models import CanonicalProfile


def score_profile(profile: CanonicalProfile) -> float:
    if not profile.provenance:
        return 0.0

    field_weights = {
        "full_name": 0.15,
        "emails": 0.15,
        "phones": 0.1,
        "headline": 0.08,
        "skills": 0.12,
        "experience": 0.15,
        "education": 0.1,
        "location": 0.05,
        "years_experience": 0.05,
        "links.linkedin": 0.025,
        "links.github": 0.025,
    }

    best_by_field: dict[str, float] = {}
    for entry in profile.provenance:
        confidence = entry.confidence if entry.confidence is not None else 0.0
        current = best_by_field.get(entry.field, 0.0)
        if confidence > current:
            best_by_field[entry.field] = confidence

    weighted_sum = 0.0
    total_weight = 0.0
    for field, weight in field_weights.items():
        if field in best_by_field:
            weighted_sum += best_by_field[field] * weight
            total_weight += weight
        elif field.startswith("links.") and profile.links.model_dump().get(field.split(".", 1)[1]):
            weighted_sum += 0.5 * weight
            total_weight += weight

    if total_weight == 0:
        return round(sum(best_by_field.values()) / max(len(best_by_field), 1), 3)

    overall = weighted_sum / total_weight

    source_count = len({entry.source for entry in profile.provenance})
    if source_count >= 3:
        overall = min(1.0, overall + 0.05)
    elif source_count == 1:
        overall = max(0.0, overall - 0.05)

    return round(min(1.0, max(0.0, overall)), 3)
