"""
Tests specifically validating Requirement 3:
"Accept missing sensor values as NULL rather than replacing them with zero."
"""

from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models import SensorReading, User
from Backend.repositories import SensorReadingRepository
from Backend.schemas import (
    SensorReadingBatchCreate,
    SensorReadingCreate,
    SensorReadingBase,
)


def test_missing_sensor_values_stored_as_null(db: Session, sample_user: User):
    """
    Assert that omitted/missing sensor telemetry fields are stored as SQL NULL
    and are NEVER coerced to 0 or 0.0.
    """
    reading_in = SensorReadingCreate(
        user_id=sample_user.id,
        timestamp=now_utc(),
        heart_rate=None,  # Missing sensor channel
        eda=None,         # Missing sensor channel
        skin_temperature=None,
        blood_oxygen=None,
        respiratory_rate=None,
        step_count=None,
        device_id="TEST_SENSOR_OFFLINE",
    )

    created = SensorReadingRepository.create(db, reading_in)

    # 1. ORM level validation
    assert created.id is not None
    assert created.heart_rate is None
    assert created.heart_rate != 0
    assert created.heart_rate != 0.0
    assert created.eda is None
    assert created.eda != 0.0
    assert created.skin_temperature is None
    assert created.blood_oxygen is None
    assert created.respiratory_rate is None
    assert created.step_count is None

    # 2. Raw SQL level verification directly on the SQLite database
    raw_query = text(
        "SELECT heart_rate, eda, skin_temperature, blood_oxygen, respiratory_rate, step_count "
        "FROM sensor_readings WHERE id = :id"
    )
    row = db.execute(raw_query, {"id": created.id}).fetchone()
    assert row is not None

    for col_idx, col_value in enumerate(row):
        assert col_value is None, f"Column index {col_idx} was {col_value} instead of SQL NULL"


def test_partial_sensor_values_preserve_nulls(db: Session, sample_user: User):
    """
    When some sensors are active and others are disconnected,
    active values must be preserved while missing channels remain NULL.
    """
    reading_in = SensorReadingCreate(
        user_id=sample_user.id,
        timestamp=now_utc(),
        heart_rate=78.5,  # Active sensor
        eda=None,         # Disconnected electrode
        skin_temperature=33.1,  # Active sensor
        blood_oxygen=None,      # Disconnected SpO2 clip
        respiratory_rate=16.0,
        step_count=None,
    )

    created = SensorReadingRepository.create(db, reading_in)

    assert created.heart_rate == 78.5
    assert created.eda is None
    assert created.skin_temperature == 33.1
    assert created.blood_oxygen is None
    assert created.respiratory_rate == 16.0
    assert created.step_count is None


def test_batch_ingest_preserves_nulls(db: Session, sample_user: User):
    """
    Batch telemetry creation must preserve NULL across multiple samples.
    """
    now = now_utc()
    batch = SensorReadingBatchCreate(
        user_id=sample_user.id,
        readings=[
            SensorReadingBase(
                timestamp=now - timedelta(seconds=10),
                heart_rate=72.0,
                eda=None,
            ),
            SensorReadingBase(
                timestamp=now,
                heart_rate=None,
                eda=3.4,
            ),
        ],
    )

    created_readings = SensorReadingRepository.bulk_create(db, batch)
    assert len(created_readings) == 2

    assert created_readings[0].heart_rate == 72.0
    assert created_readings[0].eda is None

    assert created_readings[1].heart_rate is None
    assert created_readings[1].eda == 3.4
