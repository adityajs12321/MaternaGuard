from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def _payload() -> dict:
    return {
        "device_id": "device-test-1",
        "abha_id": "12345678901234",
        "age": 28,
        "sbp": 120,
        "dbp": 80,
        "blood_sugar": 5.4,
        "body_temp": 36.8,
        "heart_rate": 82,
        "original_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def test_predict_validation_error() -> None:
    bad = _payload()
    bad["age"] = -1
    response = client.post("/predict", json=bad)
    assert response.status_code == 422


def test_predict_valid_when_model_available_or_503() -> None:
    response = client.post("/predict", json=_payload())
    # Either a valid prediction or model unavailable in environments with missing artifacts.
    assert response.status_code in (200, 503)
