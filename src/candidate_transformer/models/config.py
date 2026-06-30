"""Runtime output projection configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OutputFieldSpec(BaseModel):
    path: str
    from_: str | None = Field(default=None, alias="from")
    type: Literal["string", "number", "string[]", "object", "boolean"] = "string"
    required: bool = False
    normalize: Literal["E164", "canonical", "none"] | None = None

    model_config = {"populate_by_name": True}


class OutputConfig(BaseModel):
    fields: list[OutputFieldSpec] = Field(default_factory=list)
    include_confidence: bool = False
    include_provenance: bool = False
    on_missing: Literal["null", "omit", "error"] = "null"
