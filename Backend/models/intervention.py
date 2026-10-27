"""
Intervention model for MindEase-AI.
Tracks therapeutic micro-interventions (breathing, grounding, mindfulness) delivered to users.
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.episode import Episode
    from Backend.models.notification_event import NotificationEvent
    from Backend.models.user import User


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    episode_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("episodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # e.g., box_breathing, grounding_54321, mindful_pause, guided_audio, emergency_call
    intervention_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # e.g., suggested, accepted, in_progress, completed, skipped, rejected
    status: Mapped[str] = mapped_column(
        String(50), default="suggested", nullable=False
    )

    start_time: Mapped[Optional[UTCDateTime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    end_time: Mapped[Optional[UTCDateTime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # User satisfaction rating 1 to 5
    user_feedback_rating: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    user: Mapped["User"] = relationship("User", back_populates="interventions")
    episode: Mapped[Optional["Episode"]] = relationship(
        "Episode", back_populates="interventions"
    )
    notification_events: Mapped[List["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="intervention", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "user_feedback_rating IS NULL OR (user_feedback_rating >= 1 AND user_feedback_rating <= 5)",
            name="ck_intervention_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Intervention(id={self.id}, user_id='{self.user_id}', "
            f"type='{self.intervention_type}', status='{self.status}')>"
        )
