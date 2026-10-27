"""
Integration tests for FastAPI endpoints backed by isolated database session.
"""

from fastapi.testclient import TestClient

from Backend.models import User


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_create_user_api(client: TestClient):
    payload = {
        "email": "api.user@mindease.ai",
        "username": "api_user_99",
        "full_name": "API Test User",
    }
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["email"] == "api.user@mindease.ai"


def test_ingest_sensor_reading_with_nulls_api(client: TestClient, sample_user: User):
    """
    Ensure API accepts missing sensor metrics as NULL rather than 0.
    """
    payload = {
        "user_id": sample_user.id,
        "heart_rate": 75.0,
        "eda": None,  # Intentionally null
        "skin_temperature": None,
        "blood_oxygen": 98.0,
    }
    response = client.post("/api/v1/sensors/readings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["heart_rate"] == 75.0
    assert data["eda"] is None
    assert data["skin_temperature"] is None
    assert data["blood_oxygen"] == 98.0


def test_notification_flow_api(client: TestClient, sample_user: User):
    """
    Ensure notification starts as simulated and can only become confirmed
    delivered through the confirm-delivery endpoint.
    """
    # 1. Create notification
    create_payload = {
        "user_id": sample_user.id,
        "recipient": "+1-555-0100",
        "notification_channel": "sms",
        "notification_type": "panic_alert",
        "message_content": "Simulated panic alert test",
    }
    response = client.post("/api/v1/notifications", json=create_payload)
    assert response.status_code == 201
    notif = response.json()
    assert notif["is_simulated"] is True
    assert notif["status"] == "simulated"

    # 2. Confirm delivery
    confirm_payload = {
        "delivery_provider": "AWS_SNS",
        "delivery_confirmation_id": "SNS_MSG_9921",
        "details": {"status": "SUCCESS"},
    }
    confirm_resp = client.post(
        f"/api/v1/notifications/{notif['id']}/confirm-delivery",
        json=confirm_payload,
    )
    assert confirm_resp.status_code == 200
    updated_notif = confirm_resp.json()
    assert updated_notif["is_simulated"] is False
    assert updated_notif["status"] == "delivered"
    assert updated_notif["delivery_provider"] == "AWS_SNS"
