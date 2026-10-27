"""
Unit tests for repository layer CRUD functions.
"""

from datetime import timedelta
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models import User
from Backend.repositories import (
    BaselineRepository,
    EpisodeRepository,
    InterventionRepository,
    UserRepository,
)
from Backend.schemas import (
    BaselineCreate,
    BaselineUpdate,
    EpisodeCreate,
    EpisodeUpdate,
    InterventionCreate,
    UserCreate,
    UserUpdate,
)


def test_user_repository_crud(db: Session):
    # Create
    user_in = UserCreate(
        email="maya@mindease.ai",
        username="maya_zen",
        full_name="Maya Lin",
    )
    user = UserRepository.create(db, user_in)
    assert user.id is not None
    assert user.email == "maya@mindease.ai"

    # Get by ID & Email
    assert UserRepository.get_by_id(db, user.id) is not None
    assert UserRepository.get_by_email(db, "maya@mindease.ai") is not None
    assert UserRepository.get_by_username(db, "maya_zen") is not None

    # Update
    updated = UserRepository.update(
        db, user.id, UserUpdate(full_name="Maya Lin-Zhang")
    )
    assert updated.full_name == "Maya Lin-Zhang"

    # List
    users = UserRepository.list(db)
    assert any(u.id == user.id for u in users)

    # Delete
    deleted = UserRepository.delete(db, user.id)
    assert deleted is True
    assert UserRepository.get_by_id(db, user.id) is None


def test_baseline_repository_crud(db: Session, sample_user: User):
    now = now_utc()
    baseline = BaselineRepository.create(
        db,
        BaselineCreate(
            user_id=sample_user.id,
            baseline_heart_rate=65.0,
            baseline_eda=1.8,
            window_start=now - timedelta(days=3),
            window_end=now,
            is_active=True,
        ),
    )
    assert baseline.id is not None

    active = BaselineRepository.get_active(db, sample_user.id)
    assert active is not None
    assert active.baseline_heart_rate == 65.0

    # Update baseline
    updated = BaselineRepository.update(
        db, baseline.id, BaselineUpdate(baseline_heart_rate=64.0)
    )
    assert updated.baseline_heart_rate == 64.0


def test_episode_repository_crud(db: Session, sample_user: User):
    now = now_utc()
    episode = EpisodeRepository.create(
        db,
        EpisodeCreate(
            user_id=sample_user.id,
            start_time=now - timedelta(minutes=10),
            peak_severity=8.2,
            episode_type="panic_attack",
            status="ongoing",
            trigger_description="Crowded space panic trigger",
        ),
    )
    assert episode.id is not None
    assert episode.status == "ongoing"

    # Resolve episode
    resolved = EpisodeRepository.resolve(
        db, episode.id, notes="Patient used 5-4-3-2-1 technique."
    )
    assert resolved.status == "resolved"
    assert resolved.end_time is not None
    assert "5-4-3-2-1" in resolved.resolution_notes


def test_intervention_repository_crud(db: Session, sample_user: User):
    now = now_utc()
    intervention = InterventionRepository.create(
        db,
        InterventionCreate(
            user_id=sample_user.id,
            intervention_type="grounding_54321",
            status="in_progress",
            start_time=now - timedelta(minutes=5),
        ),
    )
    assert intervention.id is not None
    assert intervention.status == "in_progress"

    completed = InterventionRepository.complete(
        db, intervention.id, rating=5, notes="Very helpful grounding"
    )
    assert completed.status == "completed"
    assert completed.user_feedback_rating == 5
    assert completed.end_time is not None
