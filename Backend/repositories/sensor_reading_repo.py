"""
Repository for SensorReading database operations.
Explicitly guarantees missing sensor metrics are persisted as SQL NULL, never zero.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models.sensor_reading import SensorReading
from Backend.schemas.sensor_reading import SensorReadingBatchCreate, SensorReadingCreate


class SensorReadingRepository:
    @staticmethod
    def create(db: Session, reading_in: SensorReadingCreate) -> SensorReading:
        """
        Create a single sensor reading.
        Missing telemetry fields are preserved as None/NULL.
        """
        reading = SensorReading(
            user_id=reading_in.user_id,
            timestamp=reading_in.timestamp or now_utc(),
            heart_rate=reading_in.heart_rate,
            eda=reading_in.eda,
            skin_temperature=reading_in.skin_temperature,
            blood_oxygen=reading_in.blood_oxygen,
            respiratory_rate=reading_in.respiratory_rate,
            step_count=reading_in.step_count,
            device_id=reading_in.device_id,
            raw_data=reading_in.raw_data,
        )
        db.add(reading)
        db.flush()
        db.refresh(reading)
        return reading

    @staticmethod
    def bulk_create(
        db: Session, batch: SensorReadingBatchCreate
    ) -> List[SensorReading]:
        """
        Efficiently insert a batch of sensor readings for a user.
        Preserves all NULLs across sparse sensor payloads.
        """
        readings = []
        for item in batch.readings:
            reading = SensorReading(
                user_id=batch.user_id,
                timestamp=item.timestamp or now_utc(),
                heart_rate=item.heart_rate,
                eda=item.eda,
                skin_temperature=item.skin_temperature,
                blood_oxygen=item.blood_oxygen,
                respiratory_rate=item.respiratory_rate,
                step_count=item.step_count,
                device_id=item.device_id,
                raw_data=item.raw_data,
            )
            readings.append(reading)

        db.add_all(readings)
        db.flush()
        for r in readings:
            db.refresh(r)
        return readings

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.user_id == user_id)
            .order_by(SensorReading.timestamp.asc())
        )
        if start_time:
            stmt = stmt.where(SensorReading.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(SensorReading.timestamp <= end_time)
        stmt = stmt.limit(limit)

        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_latest(db: Session, user_id: str) -> Optional[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.user_id == user_id)
            .order_by(desc(SensorReading.timestamp))
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()
