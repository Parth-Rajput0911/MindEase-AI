"""
User model for MindEase-AI.
Stores identity, authentication, profile, and emergency contact details.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.baseline import Baseline
    from Backend.models.episode import Episode
    from Backend.models.intervention import Intervention
    from Backend.models.notification_event import NotificationEvent
    from Backend.models.sensor_reading import SensorReading


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Emergency contact details for critical stress/panic notifications
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    emergency_contact_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    created_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        nullable=False,
    )
    updated_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        onupdate=now_utc,
        nullable=False,
    )

    # Relationships
    sensor_readings: Mapped[List["SensorReading"]] = relationship(
        "SensorReading", back_populates="user", cascade="all, delete-orphan"
    )
    baselines: Mapped[List["Baseline"]] = relationship(
        "Baseline", back_populates="user", cascade="all, delete-orphan"
    )
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode", back_populates="user", cascade="all, delete-orphan"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", back_populates="user", cascade="all, delete-orphan"
    )
    notification_events: Mapped[List["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
