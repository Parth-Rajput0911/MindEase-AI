"""
Sensor reading model for MindEase-AI.
Stores multi-modal physiological telemetry (Heart Rate, EDA, Skin Temperature, etc.).
Missing sensor readings are preserved as NULL and NEVER coerced to zero.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.user import User


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Telemetry timestamp (UTC)
    timestamp: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        nullable=False,
        index=True,
        default=now_utc,
    )

    # Physiological metrics - explicitly nullable with NO zero defaults.
    # Requirement: Accept missing sensor values as NULL rather than replacing them with zero.
    heart_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )
    eda: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )  # Electrodermal Activity (uS)
    skin_temperature: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )  # Degrees Celsius
    blood_oxygen: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )  # SpO2 percentage
    respiratory_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )  # Breaths per minute
    step_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )

    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sensor_readings")

    # Table arguments: composite index for fast time-range lookups per user and integrity constraints
    __table_args__ = (
        Index("ix_sensor_readings_user_timestamp", "user_id", "timestamp"),
        CheckConstraint(
            "heart_rate IS NULL OR heart_rate > 0",
            name="ck_sensor_hr_positive",
        ),
        CheckConstraint(
            "blood_oxygen IS NULL OR (blood_oxygen >= 0 AND blood_oxygen <= 100)",
            name="ck_sensor_spo2_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorReading(id={self.id}, user_id='{self.user_id}', "
            f"timestamp='{self.timestamp}', hr={self.heart_rate}, eda={self.eda})>"
        )
