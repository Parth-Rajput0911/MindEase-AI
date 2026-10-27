"""
Seed script for MindEase-AI database layer.
Creates one synthetic demo user and clearly synthetic sample data across all models:
- User (Synthetic demo profile with emergency contact)
- Baselines (Synthetic calibrated resting profile)
- Sensor Readings (Synthetic time-series telemetry with deliberate NULL values)
- Episode (Synthetic acute stress event)
- Intervention (Synthetic completed box breathing exercise with rating)
- Notification Events (Synthetic alerts marked is_simulated=True per Req #12)
"""

from datetime import datetime, timedelta, timezone
import os
import sys
from typing import Optional
from sqlalchemy.orm import Session

# Ensure workspace root and Backend/ are on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from Backend.database import SessionLocal, init_db, now_utc
from Backend.models import (
    Baseline,
    Episode,
    Intervention,
    NotificationEvent,
    SensorReading,
    User,
)
from Backend.repositories import (
    BaselineRepository,
    EpisodeRepository,
    InterventionRepository,
    NotificationEventRepository,
    SensorReadingRepository,
    UserRepository,
)
from Backend.schemas import (
    BaselineCreate,
    EpisodeCreate,
    InterventionCreate,
    NotificationEventCreate,
    SensorReadingBatchCreate,
    SensorReadingBase,
    UserCreate,
)

SYNTHETIC_EMAIL = "demo.synthetic@mindease.ai"
SYNTHETIC_USERNAME = "synthetic_demo_user"


def seed_database(db: Optional[Session] = None) -> User:
    """
    Populate database with a synthetic demo user and realistic sample telemetry.
    Can be run against any active SQLAlchemy session.
    """
    session_provided = db is not None
    session: Session = db if session_provided else SessionLocal()

    try:
        # Check if synthetic demo user already exists
        existing_user = UserRepository.get_by_email(session, SYNTHETIC_EMAIL)
        if existing_user:
            print(f"[Seed] Synthetic demo user already exists (id={existing_user.id}). Cleaning up old records...")
            session.delete(existing_user)
            session.flush()

        print("[Seed] Creating synthetic demo user...")
        demo_user = UserRepository.create(
            session,
            UserCreate(
                email=SYNTHETIC_EMAIL,
                username=SYNTHETIC_USERNAME,
                full_name="Synthetic MindEase Demo User",
                password="synthetic_demo_password_hash",
                is_active=True,
                emergency_contact_name="Synthetic Emergency Contact",
                emergency_contact_phone="+1-555-0199",
                emergency_contact_email="synthetic.emergency@mindease.ai",
            ),
        )

        now = now_utc()

        # 1. Baseline
        print("[Seed] Creating synthetic physiological baseline...")
        baseline = BaselineRepository.create(
            session,
            BaselineCreate(
                user_id=demo_user.id,
                baseline_heart_rate=68.5,
                baseline_eda=2.35,
                baseline_skin_temp=33.2,
                baseline_respiratory_rate=14.0,
                window_start=now - timedelta(days=7),
                window_end=now,
                is_active=True,
                calibration_status="calibrated",
            ),
        )

        # 2. Sensor Readings (Telemetry with deliberate NULLs to verify Requirement 3)
        print("[Seed] Creating synthetic sensor telemetry series (with deliberate NULL values)...")
        readings = [
            # Reading 1: Normal resting state (all channels intact)
            SensorReadingBase(
                timestamp=now - timedelta(minutes=60),
                heart_rate=69.0,
                eda=2.40,
                skin_temperature=33.3,
                blood_oxygen=98.5,
                respiratory_rate=14.2,
                step_count=12,
                device_id="SYNTHETIC_WATCH_01",
                raw_data={"source": "synthetic_simulator", "motion_state": "sedentary"},
            ),
            # Reading 2: Stress onset beginning - heart rate climbing
            SensorReadingBase(
                timestamp=now - timedelta(minutes=45),
                heart_rate=88.5,
                eda=4.80,
                skin_temperature=32.8,
                blood_oxygen=98.0,
                respiratory_rate=17.5,
                step_count=0,
                device_id="SYNTHETIC_WATCH_01",
            ),
            # Reading 3: Peak stress - EDA disconnected / NULL (Req #3: NULL not zero)
            SensorReadingBase(
                timestamp=now - timedelta(minutes=30),
                heart_rate=114.0,
                eda=None,  # Intentionally missing EDA telemetry
                skin_temperature=31.9,
                blood_oxygen=97.0,
                respiratory_rate=22.0,
                step_count=0,
                device_id="SYNTHETIC_WATCH_01",
                raw_data={"alert": "EDA electrode high impedance / offline"},
            ),
            # Reading 4: Optical heart rate dropout - HR is NULL (Req #3: NULL not zero)
            SensorReadingBase(
                timestamp=now - timedelta(minutes=25),
                heart_rate=None,  # Intentionally missing Optical HR telemetry
                eda=8.10,
                skin_temperature=31.7,
                blood_oxygen=None,  # Intentionally missing SpO2 telemetry
                respiratory_rate=21.0,
                step_count=0,
                device_id="SYNTHETIC_WATCH_01",
                raw_data={"alert": "Optical sensor poor skin contact"},
            ),
            # Reading 5: Post-intervention recovery - heart rate returning toward baseline
            SensorReadingBase(
                timestamp=now - timedelta(minutes=10),
                heart_rate=74.0,
                eda=3.10,
                skin_temperature=32.9,
                blood_oxygen=99.0,
                respiratory_rate=14.8,
                step_count=5,
                device_id="SYNTHETIC_WATCH_01",
            ),
        ]

        SensorReadingRepository.bulk_create(
            session,
            SensorReadingBatchCreate(user_id=demo_user.id, readings=readings),
        )

        # 3. Episode (Acute stress episode)
        print("[Seed] Creating synthetic acute stress episode...")
        episode = EpisodeRepository.create(
            session,
            EpisodeCreate(
                user_id=demo_user.id,
                baseline_id=baseline.id,
                start_time=now - timedelta(minutes=35),
                end_time=now - timedelta(minutes=15),
                peak_severity=7.8,
                episode_type="stress",
                status="resolved",
                trigger_description="[SYNTHETIC] High stress event detected by sustained tachycardia and skin conductance spike.",
                resolution_notes="[SYNTHETIC] Episode resolved after 10-minute box breathing intervention.",
            ),
        )

        # 4. Intervention (Box breathing)
        print("[Seed] Creating synthetic completed intervention...")
        InterventionRepository.create(
            session,
            InterventionCreate(
                user_id=demo_user.id,
                episode_id=episode.id,
                intervention_type="box_breathing",
                status="completed",
                start_time=now - timedelta(minutes=25),
                end_time=now - timedelta(minutes=15),
                duration_seconds=600,
                user_feedback_rating=5,
                user_notes="[SYNTHETIC] Felt significant relief; heart rate returned toward 74 BPM.",
            ),
        )

        # 5. Notification Events (Requirement 12: Must remain is_simulated=True)
        print("[Seed] Creating synthetic notification events (marked is_simulated=True)...")
        NotificationEventRepository.create(
            session,
            NotificationEventCreate(
                user_id=demo_user.id,
                episode_id=episode.id,
                recipient="synthetic_demo_user",
                notification_channel="in_app",
                notification_type="breathing_reminder",
                message_content="[SYNTHETIC DEMO] Heart rate elevation detected. Tap here to start a 4-7-8 box breathing exercise.",
                status="simulated",
                is_simulated=True,
            ),
        )
        NotificationEventRepository.create(
            session,
            NotificationEventCreate(
                user_id=demo_user.id,
                episode_id=episode.id,
                recipient="+1-555-0199 (Synthetic Emergency Contact)",
                notification_channel="sms",
                notification_type="panic_alert",
                message_content="[SYNTHETIC DEMO] MindEase-AI alert: High stress threshold reached. User initiated calming intervention.",
                status="simulated",
                is_simulated=True,
            ),
        )

        if not session_provided:
            session.commit()

        print(f"[Seed] Successfully seeded synthetic demo data for user: {demo_user.email} (ID: {demo_user.id})")
        return demo_user

    except Exception as exc:
        if not session_provided:
            session.rollback()
        print(f"[Seed] Error seeding database: {exc}", file=sys.stderr)
        raise
    finally:
        if not session_provided:
            session.close()


if __name__ == "__main__":
    # Register models only (does NOT create tables).
    # Tables must already exist via `alembic upgrade head` before running this script.
    init_db()
    seed_database()
