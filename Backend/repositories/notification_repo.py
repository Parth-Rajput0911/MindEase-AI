"""
Repository for NotificationEvent database operations.
Requirement 12: Keep notification records marked as simulated unless a real
notification service confirms delivery.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models.notification_event import NotificationEvent
from Backend.schemas.notification_event import (
    NotificationDeliveryConfirmation,
    NotificationEventCreate,
)


class NotificationEventRepository:
    @staticmethod
    def create(
        db: Session, notification_in: NotificationEventCreate
    ) -> NotificationEvent:
        """
        Creates a notification event.
        Guarantees that notifications start as simulated (Requirement 12).
        """
        notification = NotificationEvent(
            user_id=notification_in.user_id,
            episode_id=notification_in.episode_id,
            intervention_id=notification_in.intervention_id,
            recipient=notification_in.recipient,
            notification_channel=notification_in.notification_channel,
            notification_type=notification_in.notification_type,
            message_content=notification_in.message_content,
            # Explicitly enforce simulated status
            status="simulated",
            is_simulated=True,
            sent_at=now_utc(),
        )
        db.add(notification)
        db.flush()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_by_id(db: Session, notification_id: int) -> Optional[NotificationEvent]:
        return db.get(NotificationEvent, notification_id)

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: str,
        simulated_only: Optional[bool] = None,
        limit: int = 100,
    ) -> List[NotificationEvent]:
        stmt = (
            select(NotificationEvent)
            .where(NotificationEvent.user_id == user_id)
            .order_by(NotificationEvent.created_at.desc())
        )
        if simulated_only is not None:
            stmt = stmt.where(NotificationEvent.is_simulated.is_(simulated_only))
        stmt = stmt.limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def confirm_delivery(
        db: Session,
        notification_id: int,
        confirmation: NotificationDeliveryConfirmation,
    ) -> Optional[NotificationEvent]:
        """
        Transitions a notification from simulated to confirmed delivered
        ONLY when verified provider credentials / confirmation payload is supplied.
        """
        notification = db.get(NotificationEvent, notification_id)
        if not notification:
            return None

        notification.confirm_real_delivery(
            provider=confirmation.delivery_provider,
            confirmation_id=confirmation.delivery_confirmation_id,
            details=confirmation.details,
        )
        notification.sent_at = now_utc()
        db.flush()
        db.refresh(notification)
        return notification
