"""Canonical profile and intermediate source record models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    city: str | None = None
    region: str | None = None
    country: str | None = None


class Links(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str | None = None
    title: str | None = None
    start: str | None = None
    end: str | None = None
    summary: str | None = None


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    end_year: int | None = None


class ProvenanceEntry(BaseModel):
    field: str
    source: str
    method: str
    confidence: float | None = None


class CanonicalProfile(BaseModel):
    candidate_id: str
    full_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    location: Location = Field(default_factory=Location)
    links: Links = Field(default_factory=Links)
    headline: str | None = None
    years_experience: float | None = None
    skills: list[SkillEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    provenance: list[ProvenanceEntry] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FieldValue(BaseModel):
    """A single extracted field with metadata before merge."""

    field: str
    value: Any
    source: str
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    structured: bool = False


class SourceRecord(BaseModel):
    """Normalized extraction from one input source."""

    source_id: str
    source_type: Literal["structured", "unstructured"]
    match_keys: dict[str, str] = Field(default_factory=dict)
    fields: list[FieldValue] = Field(default_factory=list)
    raw_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
