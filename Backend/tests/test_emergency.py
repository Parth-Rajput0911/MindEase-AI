"""
Unit and integration tests for MindEase-AI Emergency Service.
Validates emergency dispatch, contact alerts, database records,
and crisis helpline retrieval.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from Backend.models import User
from emergency.emergency import (
    EmergencyContact,
    EmergencyDispatchPayload,
    EmergencyService,
)


def test_emergency_hotlines_endpoint(client: TestClient):
    """Ensure hotlines endpoint returns 24/7 crisis lines and supports region filtering."""
    response = client.get("/api/v1/emergency/hotlines")
    assert response.status_code == 200
    hotlines = response.json()
    assert len(hotlines) >= 5

    # Check for core 988 and 112 lines
    numbers = [h["number"] for h in hotlines]
    assert any("988" in n for n in numbers)
    assert any("112" in n for n in numbers)

    # Check region filtering
    us_resp = client.get("/api/v1/emergency/hotlines?region=US")
    assert us_resp.status_code == 200
    us_hotlines = us_resp.json()
    assert len(us_hotlines) >= 2


def test_emergency_dispatch_api(client: TestClient, sample_user: User):
    """
    Ensure triggering emergency dispatch creates an episode, an intervention,
    simulated notifications, and returns crisis instructions.
    """
    payload = {
        "user_id": sample_user.id,
        "severity": 9.2,
        "notes": "Testing acute panic assistance API trigger",
        "channels": ["sms", "in_app"],
        "simulate_only": True,
    }
    response = client.post("/api/v1/emergency/dispatch", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["dispatch_id"].startswith("EMERG-")
    assert data["status"] == "simulated_dispatched"
    assert data["user_id"] == sample_user.id
    assert data["episode_id"] is not None
    assert data["intervention_id"] is not None
    assert data["alerts_created"] >= 1
    assert len(data["hotlines"]) >= 3
    assert len(data["immediate_coping_steps"]) >= 3
    assert "911" in data["safety_disclaimer"] or "112" in data["safety_disclaimer"]

    # Verify notification records are marked as simulated
    for notif in data["notification_events"]:
        assert notif["is_simulated"] is True
        assert notif["status"] == "simulated"
        assert notif["notification_type"] == "panic_alert"


def test_emergency_dispatch_with_custom_contacts(client: TestClient, sample_user: User):
    """
    Ensure emergency dispatch notifies custom contacts provided in the request payload.
    """
    payload = {
        "user_id": sample_user.id,
        "severity": 8.0,
        "notes": "Emergency test with doctor and sister",
        "custom_contacts": [
            {
                "name": "Dr. Watson",
                "phone": "+1-555-0188",
                "relationship": "Therapist",
                "is_primary": False,
            },
            {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "relationship": "Sister",
                "is_primary": True,
            },
        ],
        "channels": ["sms", "email"],
    }
    response = client.post("/api/v1/emergency/dispatch", json=payload)
    assert response.status_code == 201
    data = response.json()

    contact_names = [c["name"] for c in data["contacts_alerted"]]
    assert "Dr. Watson" in contact_names
    assert "Jane Doe" in contact_names


def test_emergency_history_endpoint(client: TestClient, sample_user: User):
    """
    Ensure emergency dispatch history can be queried by user ID.
    """
    # 1. Trigger an alert first
    payload = {
        "user_id": sample_user.id,
        "severity": 8.7,
        "notes": "History test dispatch",
        "channels": ["sms"],
    }
    client.post("/api/v1/emergency/dispatch", json=payload)

    # 2. Retrieve history
    resp = client.get(f"/api/v1/emergency/history/{sample_user.id}")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 1
    assert history[0]["notification_type"] in ["panic_alert", "emergency_dispatch"]
