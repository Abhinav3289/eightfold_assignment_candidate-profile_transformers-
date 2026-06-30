from pathlib import Path

import pytest

from candidate_transformer.merge import merge_source_records
from candidate_transformer.models import FieldValue, SourceRecord
from candidate_transformer.normalize import canonicalize_skill, normalize_date, normalize_phone
from candidate_transformer.pipeline import run_pipeline
from candidate_transformer.project import ProjectionError, project_profile
from candidate_transformer.models import CanonicalProfile, OutputConfig, OutputFieldSpec


SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_normalize_phone_e164():
    assert normalize_phone("(415) 555-0198") == "+14155550198"
    assert normalize_phone("garbage") is None


def test_normalize_date_formats():
    assert normalize_date("Jan 2021") == "2021-01"
    assert normalize_date("2018-06") == "2018-06"
    assert normalize_date("Present") is None


def test_canonicalize_skills():
    assert canonicalize_skill("python") == "Python"
    assert canonicalize_skill("k8s") == "Kubernetes"


def test_merge_prefers_structured_over_unstructured():
    structured = SourceRecord(
        source_id="csv",
        source_type="structured",
        match_keys={"email": "a@example.com"},
        fields=[
            FieldValue(
                field="full_name",
                value="Alice Example",
                source="csv",
                method="direct_map",
                confidence=0.9,
                structured=True,
            )
        ],
    )
    unstructured = SourceRecord(
        source_id="notes",
        source_type="unstructured",
        match_keys={"email": "a@example.com"},
        fields=[
            FieldValue(
                field="full_name",
                value="Alice X",
                source="notes",
                method="heuristic",
                confidence=0.95,
                structured=False,
            )
        ],
    )
    profile = merge_source_records([structured, unstructured])
    assert profile.full_name == "Alice Example"


def test_custom_projection():
    profile = CanonicalProfile(
        candidate_id="cand_test",
        full_name="Priya Sharma",
        emails=["priya.sharma@example.com"],
        phones=["+14155550198"],
        skills=[
            {"name": "Python", "confidence": 0.8, "sources": ["ats"]},
            {"name": "AWS", "confidence": 0.7, "sources": ["ats"]},
        ],
        overall_confidence=0.82,
    )
    config = OutputConfig(
        fields=[
            OutputFieldSpec(path="full_name", type="string", required=True),
            OutputFieldSpec(path="primary_email", **{"from": "emails[0]"}, type="string", required=True),
            OutputFieldSpec(path="phone", **{"from": "phones[0]"}, type="string", normalize="E164"),
            OutputFieldSpec(path="skills", **{"from": "skills[].name"}, type="string[]", normalize="canonical"),
        ],
        include_confidence=True,
        on_missing="null",
    )
    projected = project_profile(profile, config)
    assert projected["primary_email"] == "priya.sharma@example.com"
    assert projected["phone"] == "+14155550198"
    assert "Python" in projected["skills"]


def test_projection_required_missing_raises():
    profile = CanonicalProfile(candidate_id="c1", emails=[])
    config = OutputConfig(
        fields=[
            OutputFieldSpec(path="primary_email", **{"from": "emails[0]"}, type="string", required=True),
        ],
        on_missing="error",
    )
    with pytest.raises(ProjectionError):
        project_profile(profile, config)


def test_end_to_end_pipeline():
    result = run_pipeline(
        [
            SAMPLES / "recruiter.csv",
            SAMPLES / "ats.json",
            SAMPLES / "github_profile.json",
            SAMPLES / "resume.txt",
            SAMPLES / "recruiter_notes.txt",
        ]
    )
    assert result["full_name"] == "Priya Sharma"
    assert result["emails"][0] == "priya.sharma@example.com"
    assert result["phones"][0] == "+14155550198"
    assert result["overall_confidence"] > 0
    assert len(result["skills"]) >= 3
    assert len(result["provenance"]) > 0
