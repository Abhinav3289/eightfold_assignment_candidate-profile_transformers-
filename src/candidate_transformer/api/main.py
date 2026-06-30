"""FastAPI REST API for the candidate transformer."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from candidate_transformer import __version__
from candidate_transformer.api.schemas import (
    ApiInfoResponse,
    ErrorResponse,
    HealthResponse,
    SampleTransformRequest,
    TransformResponse,
)
from candidate_transformer.api.service import (
    example_config_payload,
    parse_output_config,
    transform_samples,
    transform_uploaded_files,
)
from candidate_transformer.project import ProjectionError
from candidate_transformer.validate import ValidationFailure

DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
API_KEY = os.getenv("API_KEY", "").strip()


def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Candidate Data Transformer API",
        description="REST API for multi-source candidate profile ingestion, merge, and projection.",
        version=__version__,
        docs_url="/docs" if DEBUG else "/docs",
        redoc_url="/redoc" if DEBUG else "/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(version=__version__)

    @app.get("/api/v1/", response_model=ApiInfoResponse, tags=["system"])
    def api_info() -> ApiInfoResponse:
        return ApiInfoResponse(version=__version__)

    @app.get("/api/v1/config/example", tags=["config"], dependencies=[Depends(verify_api_key)])
    def config_example() -> dict:
        return example_config_payload()

    @app.post(
        "/api/v1/transform",
        response_model=TransformResponse,
        responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
        tags=["transform"],
        dependencies=[Depends(verify_api_key)],
    )
    async def transform_files(
        files: Annotated[list[UploadFile], File(..., description="Candidate source files")],
        config_json: Annotated[
            str | None,
            Form(description="Optional OutputConfig JSON string"),
        ] = None,
        use_custom_example: Annotated[bool, Form()] = False,
        include_provenance: Annotated[bool, Form()] = True,
        include_confidence: Annotated[bool, Form()] = True,
    ) -> TransformResponse:
        try:
            uploads: list[tuple[str, bytes]] = []
            for upload in files:
                content = await upload.read()
                if not content:
                    continue
                uploads.append((upload.filename or "upload.bin", content))

            if use_custom_example:
                from candidate_transformer.api.service import load_example_config

                output_config = load_example_config(include_provenance, include_confidence)
                output_mode = "custom"
            else:
                output_config = parse_output_config(config_json)
                if output_config is None and config_json:
                    raise ValueError("Invalid output configuration")
                if output_config is None:
                    from candidate_transformer.api.service import build_default_config

                    output_config = build_default_config(include_provenance, include_confidence)
                    output_mode = "canonical"
                else:
                    output_mode = "custom"

            result = transform_uploaded_files(uploads, output_config)
            return TransformResponse(
                source_count=len(uploads),
                output_mode=output_mode,
                data=result,
            )
        except (ProjectionError, ValidationFailure, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline processing failed. Check inputs and configuration.",
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing the request.",
            ) from None

    @app.post(
        "/api/v1/transform/samples",
        response_model=TransformResponse,
        responses={400: {"model": ErrorResponse}},
        tags=["transform"],
        dependencies=[Depends(verify_api_key)],
    )
    def transform_with_samples(
        request: SampleTransformRequest,
    ) -> TransformResponse:
        try:
            from candidate_transformer.api.service import sample_input_paths

            paths = sample_input_paths()
            result = transform_samples(
                output_config=request.output_config,
                use_custom_example=request.use_custom_example,
                include_provenance=request.include_provenance,
                include_confidence=request.include_confidence,
            )
            output_mode = "custom" if request.use_custom_example or request.output_config else "canonical"
            return TransformResponse(
                source_count=len(paths),
                output_mode=output_mode,
                data=result,
            )
        except (ProjectionError, ValidationFailure, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline processing failed using sample data.",
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing the request.",
            ) from None

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=str(exc.detail)).model_dump(),
        )

    return app


app = create_app()
