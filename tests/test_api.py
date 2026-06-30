from fastapi.testclient import TestClient

from candidate_transformer.api.main import create_app


client = TestClient(create_app())


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_api_info():
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert "endpoints" in response.json()


def test_transform_samples_default():
    response = client.post("/api/v1/transform/samples", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["full_name"] == "Priya Sharma"
    assert body["data"]["overall_confidence"] > 0


def test_transform_samples_custom_example():
    response = client.post(
        "/api/v1/transform/samples",
        json={"use_custom_example": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["output_mode"] == "custom"
    assert "primary_email" in body["data"]


def test_transform_upload():
    samples_dir = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "samples"
    with open(samples_dir / "recruiter.csv", "rb") as csv_file, open(samples_dir / "ats.json", "rb") as json_file:
        response = client.post(
            "/api/v1/transform",
            files=[
                ("files", ("recruiter.csv", csv_file, "text/csv")),
                ("files", ("ats.json", json_file, "application/json")),
            ],
        )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["full_name"] == "Priya Sharma"


def test_config_example():
    response = client.get("/api/v1/config/example")
    assert response.status_code == 200
    assert "fields" in response.json()
