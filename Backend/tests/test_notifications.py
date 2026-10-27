"""
Tests specifically validating Requirement 12:
"Keep notification records marked as simulated unless a real notification service confirms delivery."
"""

from sqlalchemy.orm import Session

from Backend.models import NotificationEvent, User
from Backend.repositories import NotificationEventRepository
from Backend.schemas import (
    NotificationDeliveryConfirmation,
    NotificationEventCreate,
)


def test_notification_starts_as_simulated(db: Session, sample_user: User):
    """
    Every new notification must be marked as simulated by default.
    """
    notification_in = NotificationEventCreate(
        user_id=sample_user.id,
        recipient="+1-555-0100",
        notification_channel="sms",
        notification_type="panic_alert",
        message_content="Stress threshold exceeded alert.",
    )

    created = NotificationEventRepository.create(db, notification_in)

    assert created.id is not None
    assert created.is_simulated is True
    assert created.status == "simulated"
    assert created.delivery_provider is None
    assert created.delivery_confirmation_id is None


def test_confirm_real_delivery(db: Session, sample_user: User):
    """
    Only when an external provider confirms delivery should the notification
    transition to is_simulated=False and status='delivered'.
    """
    notification_in = NotificationEventCreate(
        user_id=sample_user.id,
        recipient="user_push_token_abc",
        notification_channel="push",
        notification_type="breathing_reminder",
        message_content="Time for your calming breath cycle.",
    )
    created = NotificationEventRepository.create(db, notification_in)
    assert created.is_simulated is True

    # Confirm real delivery via verified provider
    confirmation = NotificationDeliveryConfirmation(
        delivery_provider="Twilio_SMS_Gateway",
        delivery_confirmation_id="SM_TWILIO_CONF_998124",
        details={"carrier": "Verizon", "segments": 1, "price_usd": "0.0075"},
    )
    updated = NotificationEventRepository.confirm_delivery(
        db, created.id, confirmation
    )

    assert updated is not None
    assert updated.is_simulated is False
    assert updated.status == "delivered"
    assert updated.delivery_provider == "Twilio_SMS_Gateway"
    assert updated.delivery_confirmation_id == "SM_TWILIO_CONF_998124"
    assert updated.delivery_details["carrier"] == "Verizon"


def test_list_notifications_by_simulation_flag(db: Session, sample_user: User):
    """
    Test filtering notifications by simulated status.
    """
    # Create two notifications
    n1 = NotificationEventRepository.create(
        db,
        NotificationEventCreate(
            user_id=sample_user.id,
            recipient="test1",
            notification_channel="in_app",
            notification_type="checkin",
            message_content="Msg 1",
        ),
    )
    n2 = NotificationEventRepository.create(
        db,
        NotificationEventCreate(
            user_id=sample_user.id,
            recipient="test2",
            notification_channel="in_app",
            notification_type="checkin",
            message_content="Msg 2",
        ),
    )

    # Deliver n2
    NotificationEventRepository.confirm_delivery(
        db,
        n2.id,
        NotificationDeliveryConfirmation(
            delivery_provider="Firebase_FCM",
            delivery_confirmation_id="FCM_MSG_8871",
        ),
    )

    simulated = NotificationEventRepository.get_by_user(
        db, sample_user.id, simulated_only=True
    )
    delivered = NotificationEventRepository.get_by_user(
        db, sample_user.id, simulated_only=False
    )

    assert len(simulated) == 1
    assert simulated[0].id == n1.id

    assert len(delivered) == 1
    assert delivered[0].id == n2.id
