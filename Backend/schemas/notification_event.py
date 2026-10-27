"""
Pydantic v2 schemas for Notification Events.
Enforces simulated status unless confirmed by external delivery provider.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationEventBase(BaseModel):
    recipient: str = Field(..., max_length=255)
    notification_channel: str = Field(..., max_length=50)  # in_app, sms, email, push
    notification_type: str = Field(..., max_length=50)     # panic_alert, breathing_reminder, etc.
    message_content: str
    status: str = Field(default="simulated", max_length=50)
    is_simulated: bool = Field(
        default=True,
        description="Must remain True unless real delivery is confirmed by provider",
    )
    episode_id: Optional[int] = None
    intervention_id: Optional[int] = None


class NotificationEventCreate(NotificationEventBase):
    user_id: str
    # Enforce default simulated status on creation
    status: str = Field(default="simulated", max_length=50)
    is_simulated: bool = Field(default=True)


class NotificationDeliveryConfirmation(BaseModel):
    """Payload provided when a real third-party service confirms message dispatch."""
    delivery_provider: str = Field(..., min_length=2, max_length=100)
    delivery_confirmation_id: str = Field(..., min_length=2, max_length=255)
    details: Optional[Dict[str, Any]] = None


class NotificationEventRead(NotificationEventBase):
    id: int
    user_id: str
    delivery_provider: Optional[str] = None
    delivery_confirmation_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivery_details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
