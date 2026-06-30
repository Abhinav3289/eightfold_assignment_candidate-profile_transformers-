from candidate_transformer.ingest import ingest_manual_form


def test_manual_ingestor_builds_source_record():
    record = ingest_manual_form(
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "(415) 555-0100",
            "skills": "python, aws",
            "company": "Example Inc",
            "title": "Engineer",
        },
        source_id="manual_test",
    )
    assert record.source_id == "manual_test"
    assert record.match_keys["email"] == "jane@example.com"
    assert any(field.field == "full_name" for field in record.fields)
    assert any(field.field == "skills" for field in record.fields)


def test_manual_pipeline_end_to_end():
    from candidate_transformer.pipeline import run_pipeline

    record = ingest_manual_form(
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "415-555-0100",
            "skills": "Python, Java",
            "headline": "Backend Engineer",
        }
    )
    result = run_pipeline(source_records=[record])
    assert result["full_name"] == "Jane Doe"
    assert result["emails"][0] == "jane@example.com"
    assert result["phones"][0] == "+14155550100"
