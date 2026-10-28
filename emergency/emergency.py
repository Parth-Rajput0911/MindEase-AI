"""
MindEase-AI Emergency Service.
Provides automated and manual emergency dispatch workflows,
contact alerting, verified crisis hotline directories,
and escalation procedures for acute panic and stress episodes.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models.episode import Episode
from Backend.models.intervention import Intervention
from Backend.models.notification_event import NotificationEvent
from Backend.models.user import User
from Backend.repositories.episode_repo import EpisodeRepository
from Backend.repositories.intervention_repo import InterventionRepository
from Backend.repositories.notification_repo import NotificationEventRepository
from Backend.repositories.user_repo import UserRepository
from Backend.schemas.episode import EpisodeCreate
from Backend.schemas.intervention import InterventionCreate
from Backend.schemas.notification_event import NotificationEventCreate, NotificationEventRead


class EmergencyContact(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    relationship: str = Field(default="Trusted contact", max_length=100)
    is_primary: bool = Field(default=False)


class EmergencyHotline(BaseModel):
    country: str
    region_code: str
    name: str
    number: str
    service_type: str  # crisis, suicide_prevention, emergency_dispatch, youth
    available: str = "24/7"
    sms_support: bool = False
    website: Optional[str] = None
    description: str


EMERGENCY_HOTLINES: List[EmergencyHotline] = [
    EmergencyHotline(
        country="United States & Canada",
        region_code="US/CA",
        name="988 Suicide & Crisis Lifeline",
        number="988",
        service_type="crisis",
        available="24/7",
        sms_support=True,
        website="https://988lifeline.org",
        description="Free and confidential support for people in distress, prevention and crisis resources.",
    ),
    EmergencyHotline(
        country="United States & Canada",
        region_code="US/CA",
        name="Crisis Text Line",
        number="Text HOME to 741741",
        service_type="crisis",
        available="24/7",
        sms_support=True,
        website="https://www.crisistextline.org",
        description="Free 24/7 crisis support via text message with trained crisis counselors.",
    ),
    EmergencyHotline(
        country="United States",
        region_code="US",
        name="Emergency Services",
        number="911",
        service_type="emergency_dispatch",
        available="24/7",
        sms_support=False,
        description="Immediate dispatch for medical, safety, or life-threatening emergencies.",
    ),
    EmergencyHotline(
        country="United Kingdom",
        region_code="UK",
        name="Samaritans Helpline",
        number="116 123",
        service_type="crisis",
        available="24/7",
        sms_support=False,
        website="https://www.samaritans.org",
        description="Whatever you are going through, a Samaritan will face it with you.",
    ),
    EmergencyHotline(
        country="United Kingdom",
        region_code="UK",
        name="NHS 111 Mental Health Services",
        number="111",
        service_type="crisis",
        available="24/7",
        sms_support=False,
        description="Urgent healthcare advice and mental health triage from the NHS.",
    ),
    EmergencyHotline(
        country="European Union",
        region_code="EU",
        name="European Emergency Number",
        number="112",
        service_type="emergency_dispatch",
        available="24/7",
        sms_support=False,
        description="All-in-one emergency service accessible free of charge anywhere in the EU.",
    ),
    EmergencyHotline(
        country="India",
        region_code="IN",
        name="Tele-MANAS National Tele-Mental Health Programme",
        number="14416 / 1800-891-4416",
        service_type="crisis",
        available="24/7",
        sms_support=False,
        website="https://telemanas.mohfw.gov.in",
        description="Government of India 24/7 free mental health counseling helpline in multiple languages.",
    ),
    EmergencyHotline(
        country="India",
        region_code="IN",
        name="National Emergency Support System",
        number="112",
        service_type="emergency_dispatch",
        available="24/7",
        sms_support=False,
        description="Unified emergency helpline for police, fire, and medical ambulance emergencies in India.",
    ),
    EmergencyHotline(
        country="International",
        region_code="GLOBAL",
        name="Befrienders Worldwide",
        number="Online Directory",
        service_type="crisis",
        available="24/7",
        sms_support=False,
        website="https://www.befrienders.org",
        description="Global network of emotional support centers operating across 32 countries.",
    ),
]


class EmergencyDispatchPayload(BaseModel):
    user_id: Optional[str] = Field(
        None,
        description="Target user ID. If omitted, links to the active demo profile.",
    )
    episode_id: Optional[int] = Field(
        None,
        description="Associated episode ID if triggering from an ongoing stress/panic event.",
    )
    severity: float = Field(
        default=8.5,
        ge=0.0,
        le=10.0,
        description="Reported severity scale (0-10).",
    )
    notes: Optional[str] = Field(
        default="User requested urgent assistance via MindEase-AI emergency dispatch.",
        max_length=500,
    )
    location_hint: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional approximate location context for trusted contacts.",
    )
    custom_contacts: Optional[List[EmergencyContact]] = Field(
        default=None,
        description="Optional list of custom or local contacts to notify.",
    )
    channels: List[str] = Field(
        default=["sms", "in_app"],
        description="Channels to dispatch across (sms, email, in_app).",
    )
    simulate_only: bool = Field(
        default=True,
        description="Prototypes default to simulated alerts to prevent accidental dispatches.",
    )


class EmergencyDispatchResult(BaseModel):
    dispatch_id: str
    status: str  # "simulated_dispatched", "delivered"
    timestamp: datetime
    user_id: str
    user_name: str
    episode_id: Optional[int] = None
    intervention_id: Optional[int] = None
    alerts_created: int
    contacts_alerted: List[Dict[str, Any]]
    notification_events: List[NotificationEventRead]
    hotlines: List[EmergencyHotline]
    immediate_coping_steps: List[str]
    safety_disclaimer: str


class EmergencyService:
    """
    Emergency Service handling crisis contact escalation,
    audit records in database, and emergency resources.
    """

    @staticmethod
    def get_hotlines(region: Optional[str] = None) -> List[EmergencyHotline]:
        """Return verified crisis hotlines, optionally filtered by region code."""
        if not region:
            return EMERGENCY_HOTLINES
        r_upper = region.strip().upper()
        return [
            h
            for h in EMERGENCY_HOTLINES
            if r_upper in h.region_code.upper().split("/")
            or r_upper in h.country.upper()
            or h.region_code.upper() in ("GLOBAL", "ALL")
        ]

    @classmethod
    def dispatch(
        cls,
        db: Session,
        payload: EmergencyDispatchPayload,
    ) -> EmergencyDispatchResult:
        """
        Executes an emergency dispatch workflow:
        1. Resolves user profile (or demo user).
        2. Ensures an active panic/stress episode exists and is tracked.
        3. Records an emergency intervention ("emergency_call").
        4. Gathers registered user contacts + custom provided contacts.
        5. Emits NotificationEvent records for each contact & channel (Requirement 12: defaults to simulated).
        6. Returns structured response with hotlines and grounding steps.
        """
        dispatch_id = f"EMERG-{uuid.uuid4().hex[:8].upper()}"
        now = now_utc()

        # 1. Resolve user
        user: Optional[User] = None
        if payload.user_id:
            user = UserRepository.get_by_id(db, payload.user_id)

        if not user:
            # Fall back to demo user or find first available user
            user = UserRepository.get_by_email(db, "demo.synthetic@mindease.ai")
            if not user:
                # Retrieve any active user
                user = db.query(User).filter(User.is_active.is_(True)).first()

        if not user:
            # Create a fallback demo user if table is empty
            user = User(
                email="demo.synthetic@mindease.ai",
                username="demo_user",
                full_name="MindEase Demo User",
                emergency_contact_name="Dr. Sarah Jenkins (Caregiver)",
                emergency_contact_phone="+1-555-0199",
                emergency_contact_email="caregiver@mindease.ai",
            )
            db.add(user)
            db.flush()
            db.refresh(user)

        # 2. Resolve or create episode
        episode_id = payload.episode_id
        if episode_id is None:
            new_episode = Episode(
                user_id=user.id,
                start_time=now,
                peak_severity=payload.severity,
                episode_type="panic_attack" if payload.severity >= 7.5 else "stress",
                status="ongoing",
                trigger_description=f"[{dispatch_id}] Acute assistance triggered by user: {payload.notes}",
            )
            db.add(new_episode)
            db.flush()
            db.refresh(new_episode)
            episode_id = new_episode.id
        else:
            existing_episode = EpisodeRepository.get_by_id(db, episode_id)
            if existing_episode and existing_episode.status == "ongoing":
                existing_episode.peak_severity = max(
                    existing_episode.peak_severity or 0.0, payload.severity
                )

        # 3. Record emergency intervention
        intervention = Intervention(
            user_id=user.id,
            episode_id=episode_id,
            intervention_type="emergency_call",
            status="suggested",
            start_time=now,
            user_notes=payload.notes,
        )
        db.add(intervention)
        db.flush()
        db.refresh(intervention)

        # 4. Resolve contacts
        contacts_to_notify: List[EmergencyContact] = []

        # User's registered emergency contact
        if user.emergency_contact_name and (
            user.emergency_contact_phone or user.emergency_contact_email
        ):
            contacts_to_notify.append(
                EmergencyContact(
                    name=user.emergency_contact_name,
                    phone=user.emergency_contact_phone,
                    email=user.emergency_contact_email,
                    relationship="Primary Emergency Contact",
                    is_primary=True,
                )
            )

        # Append custom contacts provided in payload
        if payload.custom_contacts:
            for cc in payload.custom_contacts:
                if not any(
                    existing.phone == cc.phone and existing.name == cc.name
                    for existing in contacts_to_notify
                ):
                    contacts_to_notify.append(cc)

        # Fallback if no contacts found
        if not contacts_to_notify:
            contacts_to_notify.append(
                EmergencyContact(
                    name=user.emergency_contact_name or "Emergency Support Contact",
                    phone=user.emergency_contact_phone or "+1-555-0199",
                    email=user.emergency_contact_email or "emergency@mindease.ai",
                    relationship="Default Support Placeholder",
                    is_primary=True,
                )
            )

        # 5. Dispatch notifications
        created_events: List[NotificationEvent] = []
        contacts_alerted_summary: List[Dict[str, Any]] = []

        user_display_name = user.full_name or user.username or "MindEase User"
        location_msg = f" Location hint: {payload.location_hint}." if payload.location_hint else ""

        for contact in contacts_to_notify:
            for channel in payload.channels:
                recipient = contact.phone if channel == "sms" else (contact.email or contact.name)
                if not recipient:
                    continue

                message_text = (
                    f"[MindEase-AI SOS Alert] Urgent: {user_display_name} has triggered an emergency alert. "
                    f"Reported severity: {payload.severity}/10. Note: {payload.notes}.{location_msg} "
                    f"Please check in immediately."
                )

                notification_data = NotificationEventCreate(
                    user_id=user.id,
                    episode_id=episode_id,
                    intervention_id=intervention.id,
                    recipient=f"{contact.name} ({recipient})",
                    notification_channel=channel,
                    notification_type="panic_alert",
                    message_content=message_text,
                    status="simulated",
                    is_simulated=True,
                )

                event = NotificationEventRepository.create(db, notification_data)
                created_events.append(event)

            contacts_alerted_summary.append(
                {
                    "name": contact.name,
                    "relationship": contact.relationship,
                    "channels": payload.channels,
                    "status": "simulated_sent" if payload.simulate_only else "queued",
                }
            )

        db.commit()

        # 6. Immediate coping instructions
        coping_steps = [
            "1. Ground Your Body: Place both feet firmly on the floor. Unclench your jaw and gently lower your shoulders.",
            "2. Paced Breathing: Inhale slowly through your nose for 4 seconds, then exhale gently through pursed lips for 6 seconds.",
            "3. 5-4-3-2-1 Sensory Reset: Acknowledge 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.",
            "4. Immediate Connection: Call or text a trusted friend, crisis line (988), or local emergency responders (911/112). You do not have to be alone.",
        ]

        safety_disclaimer = (
            "MindEase-AI is an autonomous wellness support prototype and NOT a replacement for emergency healthcare or 911/112 dispatch. "
            "If you or someone around you is in immediate physical danger, experiencing chest pain, or having severe thoughts of self-harm, "
            "please immediately dial 911 (US/Canada), 112 (EU/India), 999 (UK), or your local emergency dispatch service."
        )

        return EmergencyDispatchResult(
            dispatch_id=dispatch_id,
            status="simulated_dispatched" if payload.simulate_only else "dispatched",
            timestamp=now,
            user_id=user.id,
            user_name=user_display_name,
            episode_id=episode_id,
            intervention_id=intervention.id,
            alerts_created=len(created_events),
            contacts_alerted=contacts_alerted_summary,
            notification_events=[NotificationEventRead.model_validate(e) for e in created_events],
            hotlines=cls.get_hotlines(),
            immediate_coping_steps=coping_steps,
            safety_disclaimer=safety_disclaimer,
        )

    @staticmethod
    def get_user_emergency_history(
        db: Session, user_id: str, limit: int = 50
    ) -> List[NotificationEventRead]:
        """Fetch past emergency and panic alerts for a specific user."""
        events = (
            db.query(NotificationEvent)
            .filter(
                NotificationEvent.user_id == user_id,
                NotificationEvent.notification_type.in_(["panic_alert", "emergency_dispatch"]),
            )
            .order_by(NotificationEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        return [NotificationEventRead.model_validate(e) for e in events]
