"""API request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from candidate_transformer.models import OutputConfig


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "candidate-transformer-api"
    version: str = "1.0.0"


class ApiInfoResponse(BaseModel):
    service: str = "candidate-transformer-api"
    version: str = "1.0.0"
    docs: str = "/docs"
    endpoints: list[str] = Field(
        default_factory=lambda: [
            "GET /health",
            "GET /api/v1/",
            "POST /api/v1/transform",
            "POST /api/v1/transform/samples",
            "GET /api/v1/config/example",
        ]
    )


class TransformResponse(BaseModel):
    success: bool = True
    source_count: int
    output_mode: Literal["canonical", "custom"]
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    success: bool = False
    detail: str


class SampleTransformRequest(BaseModel):
    output_config: OutputConfig | None = None
    use_custom_example: bool = False
    include_provenance: bool = True
    include_confidence: bool = True
