"""
Repository for Intervention database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models.intervention import Intervention
from Backend.schemas.intervention import InterventionCreate, InterventionUpdate


class InterventionRepository:
    @staticmethod
    def create(db: Session, intervention_in: InterventionCreate) -> Intervention:
        intervention = Intervention(
            user_id=intervention_in.user_id,
            episode_id=intervention_in.episode_id,
            intervention_type=intervention_in.intervention_type,
            status=intervention_in.status,
            start_time=intervention_in.start_time,
            end_time=intervention_in.end_time,
            duration_seconds=intervention_in.duration_seconds,
            user_feedback_rating=intervention_in.user_feedback_rating,
            user_notes=intervention_in.user_notes,
        )
        db.add(intervention)
        db.flush()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def get_by_id(db: Session, intervention_id: int) -> Optional[Intervention]:
        return db.get(Intervention, intervention_id)

    @staticmethod
    def get_by_user(
        db: Session, user_id: str, status: Optional[str] = None
    ) -> List[Intervention]:
        stmt = (
            select(Intervention)
            .where(Intervention.user_id == user_id)
            .order_by(Intervention.created_at.desc())
        )
        if status:
            stmt = stmt.where(Intervention.status == status)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(
        db: Session, intervention_id: int, intervention_update: InterventionUpdate
    ) -> Optional[Intervention]:
        intervention = db.get(Intervention, intervention_id)
        if not intervention:
            return None

        update_data = intervention_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(intervention, field, value)

        db.flush()
        db.refresh(intervention)
        return intervention

    @staticmethod
    def complete(
        db: Session,
        intervention_id: int,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> Optional[Intervention]:
        intervention = db.get(Intervention, intervention_id)
        if not intervention:
            return None

        intervention.status = "completed"
        intervention.end_time = now_utc()
        if rating is not None:
            intervention.user_feedback_rating = rating
        if notes:
            intervention.user_notes = notes
        if duration_seconds is not None:
            intervention.duration_seconds = duration_seconds
        elif intervention.start_time:
            delta = intervention.end_time - intervention.start_time
            intervention.duration_seconds = int(delta.total_seconds())

        db.flush()
        db.refresh(intervention)
        return intervention
