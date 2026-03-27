from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def _item(device_id: str) -> dict:
    return {
        "device_id": device_id,
        "abha_id": "12345678901234",
        "age": 29,
        "sbp": 126,
        "dbp": 82,
        "blood_sugar": 5.9,
        "body_temp": 36.7,
        "heart_rate": 80,
        "original_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def test_sync_empty_list() -> None:
    response = client.post("/sync", json={"assessments": []})
    assert response.status_code == 200
    body = response.json()
    assert body["synced_count"] == 0


def test_sync_two_records() -> None:
    payload = {"assessments": [_item("sync-device-1"), _item("sync-device-2")]}
    response = client.post("/sync", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["synced_count"] >= 1
