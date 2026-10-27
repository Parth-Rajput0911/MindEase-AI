"""
Notification event model for MindEase-AI.
Tracks notifications dispatched to users, emergency contacts, or caregivers.
Requirement 12: Keep notification records marked as simulated unless a real
notification service confirms delivery.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.episode import Episode
    from Backend.models.intervention import Intervention
    from Backend.models.user import User


class NotificationEvent(Base):
    __tablename__ = "notification_events"

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
    intervention_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("interventions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_channel: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # in_app, sms, email, push, webhook
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # panic_alert, breathing_reminder, checkin, emergency_dispatch
    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Requirement 12: Defaults to "simulated" and is_simulated=True
    status: Mapped[str] = mapped_column(
        String(50), default="simulated", nullable=False
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Filled ONLY when a verified real provider delivers the notification
    delivery_provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    delivery_confirmation_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    sent_at: Mapped[Optional[UTCDateTime]] = mapped_column(
        UTCDateTime, nullable=True
    )
    delivery_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    created_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_events")
    episode: Mapped[Optional["Episode"]] = relationship(
        "Episode", back_populates="notification_events"
    )
    intervention: Mapped[Optional["Intervention"]] = relationship(
        "Intervention", back_populates="notification_events"
    )

    __table_args__ = (
        Index("ix_notification_events_status", "status"),
        Index("ix_notification_events_user_created", "user_id", "created_at"),
    )

    def confirm_real_delivery(
        self, provider: str, confirmation_id: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Marks notification as real and confirmed delivered by an external service.
        """
        self.is_simulated = False
        self.status = "delivered"
        self.delivery_provider = provider
        self.delivery_confirmation_id = confirmation_id
        if details:
            self.delivery_details = details

    def __repr__(self) -> str:
        return (
            f"<NotificationEvent(id={self.id}, user_id='{self.user_id}', "
            f"type='{self.notification_type}', simulated={self.is_simulated}, status='{self.status}')>"
        )
