"""
Unit tests for SQLAlchemy 2.x models, constraints, relationships, and cascades.
"""

from datetime import timedelta
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models import (
    Baseline,
    Episode,
    Intervention,
    NotificationEvent,
    SensorReading,
    User,
)


def test_create_user_model(db: Session):
    user = User(
        email="alex@mindease.ai",
        username="alex_m",
        full_name="Alex Mercer",
        emergency_contact_name="Dana Mercer",
        emergency_contact_phone="+1-555-0144",
    )
    db.add(user)
    db.flush()
    assert user.id is not None
    assert len(user.id) == 36  # Valid UUID
    assert user.created_at is not None
    assert user.is_active is True


def test_user_unique_constraints(db: Session, sample_user: User):
    duplicate_email_user = User(
        email=sample_user.email,
        username="another_username",
    )
    db.add(duplicate_email_user)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_cascading_delete(db: Session, sample_user: User):
    """
    Test that deleting a User cascades to delete all linked sensor readings,
    baselines, episodes, interventions, and notification events.
    """
    now = now_utc()

    # Create one of each related entity
    reading = SensorReading(user_id=sample_user.id, timestamp=now, heart_rate=72.0)
    baseline = Baseline(
        user_id=sample_user.id,
        baseline_heart_rate=70.0,
        window_start=now - timedelta(days=1),
        window_end=now,
    )
    db.add_all([reading, baseline])
    db.flush()

    episode = Episode(
        user_id=sample_user.id,
        baseline_id=baseline.id,
        start_time=now,
        peak_severity=5.0,
    )
    db.add(episode)
    db.flush()

    intervention = Intervention(
        user_id=sample_user.id,
        episode_id=episode.id,
        intervention_type="box_breathing",
    )
    notification = NotificationEvent(
        user_id=sample_user.id,
        episode_id=episode.id,
        recipient="user",
        notification_channel="in_app",
        notification_type="breathing_reminder",
        message_content="Breathe",
    )
    db.add_all([intervention, notification])
    db.flush()

    # Ensure records exist
    reading_id = reading.id
    episode_id = episode.id
    assert db.get(SensorReading, reading_id) is not None
    assert db.get(Episode, episode_id) is not None

    # Delete User
    db.delete(sample_user)
    db.flush()

    # Verify cascading deletion
    assert db.get(SensorReading, reading_id) is None
    assert db.get(Baseline, baseline.id) is None
    assert db.get(Episode, episode_id) is None
    assert db.get(Intervention, intervention.id) is None
    assert db.get(NotificationEvent, notification.id) is None


def test_episode_severity_range_constraint(db: Session, sample_user: User):
    """Episode peak_severity must be between 0.0 and 10.0."""
    now = now_utc()
    invalid_episode = Episode(
        user_id=sample_user.id,
        start_time=now,
        peak_severity=15.0,  # Invalid: > 10.0
    )
    db.add(invalid_episode)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_intervention_rating_constraint(db: Session, sample_user: User):
    """Intervention user_feedback_rating must be between 1 and 5."""
    invalid_intervention = Intervention(
        user_id=sample_user.id,
        intervention_type="guided_meditation",
        user_feedback_rating=9,  # Invalid: > 5
    )
    db.add(invalid_intervention)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
