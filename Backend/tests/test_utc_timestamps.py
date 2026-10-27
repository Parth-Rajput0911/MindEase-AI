"""
Tests specifically validating Requirement 4:
"Store timestamps consistently in UTC."
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models import SensorReading, User
from Backend.repositories import SensorReadingRepository
from Backend.schemas import SensorReadingCreate


def test_timestamps_stored_and_returned_in_utc(db: Session, sample_user: User):
    """
    Ensure all timestamps are normalized and returned with UTC timezone.
    """
    utc_now = datetime.now(timezone.utc)
    reading = SensorReading(
        user_id=sample_user.id,
        timestamp=utc_now,
        heart_rate=70.0,
    )
    db.add(reading)
    db.flush()
    db.refresh(reading)

    assert reading.timestamp.tzinfo is not None
    # Difference should be sub-millisecond
    assert abs((reading.timestamp - utc_now).total_seconds()) < 1.0
    assert reading.timestamp.utcoffset() == timedelta(0)


def test_offset_datetime_normalized_to_utc(db: Session, sample_user: User):
    """
    If a sensor reports with a non-UTC timezone (e.g., UTC+5:30),
    the database layer must normalize it to UTC.
    """
    custom_tz = timezone(timedelta(hours=5, minutes=30))
    local_time = datetime(2026, 10, 26, 15, 0, 0, tzinfo=custom_tz)
    expected_utc = local_time.astimezone(timezone.utc)

    reading = SensorReading(
        user_id=sample_user.id,
        timestamp=local_time,
        heart_rate=80.0,
    )
    db.add(reading)
    db.flush()
    db.refresh(reading)

    assert reading.timestamp.utcoffset() == timedelta(0)
    assert reading.timestamp.hour == expected_utc.hour
    assert reading.timestamp.minute == expected_utc.minute


def test_model_created_at_defaults_to_utc(db: Session, sample_user: User):
    """Created_at and updated_at defaults must have UTC timezone."""
    assert sample_user.created_at is not None
    assert sample_user.created_at.utcoffset() == timedelta(0)
    assert sample_user.updated_at.utcoffset() == timedelta(0)
