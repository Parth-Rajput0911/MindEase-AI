"""
Episode model for MindEase-AI.
Tracks acute stress, anxiety, and panic attack episodes detected from telemetry.
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.baseline import Baseline
    from Backend.models.intervention import Intervention
    from Backend.models.notification_event import NotificationEvent
    from Backend.models.user import User


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    baseline_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("baselines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    start_time: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime, nullable=False, index=True
    )
    end_time: Mapped[Optional[UTCDateTime]] = mapped_column(
        UTCDateTime, nullable=True
    )

    # 1.0 to 10.0 scale
    peak_severity: Mapped[float] = mapped_column(Float, nullable=False)
    episode_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stress"
    )  # stress, anxiety, panic_attack
    status: Mapped[str] = mapped_column(
        String(50), default="ongoing", nullable=False
    )  # ongoing, resolved, dismissed

    trigger_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    user: Mapped["User"] = relationship("User", back_populates="episodes")
    baseline: Mapped[Optional["Baseline"]] = relationship(
        "Baseline", back_populates="episodes"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", back_populates="episode", cascade="all, delete-orphan"
    )
    notification_events: Mapped[List["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="episode", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_episodes_user_start", "user_id", "start_time"),
        CheckConstraint(
            "peak_severity >= 0.0 AND peak_severity <= 10.0",
            name="ck_episode_severity_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Episode(id={self.id}, user_id='{self.user_id}', "
            f"type='{self.episode_type}', severity={self.peak_severity}, status='{self.status}')>"
        )
