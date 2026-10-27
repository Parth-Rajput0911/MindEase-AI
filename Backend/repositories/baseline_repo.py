"""
Repository for Baseline database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.models.baseline import Baseline
from Backend.schemas.baseline import BaselineCreate, BaselineUpdate


class BaselineRepository:
    @staticmethod
    def create(db: Session, baseline_in: BaselineCreate) -> Baseline:
        baseline = Baseline(
            user_id=baseline_in.user_id,
            baseline_heart_rate=baseline_in.baseline_heart_rate,
            baseline_eda=baseline_in.baseline_eda,
            baseline_skin_temp=baseline_in.baseline_skin_temp,
            baseline_respiratory_rate=baseline_in.baseline_respiratory_rate,
            window_start=baseline_in.window_start,
            window_end=baseline_in.window_end,
            is_active=baseline_in.is_active,
            calibration_status=baseline_in.calibration_status,
        )
        db.add(baseline)
        db.flush()
        db.refresh(baseline)
        return baseline

    @staticmethod
    def get_by_id(db: Session, baseline_id: int) -> Optional[Baseline]:
        return db.get(Baseline, baseline_id)

    @staticmethod
    def get_active(db: Session, user_id: str) -> Optional[Baseline]:
        stmt = (
            select(Baseline)
            .where(Baseline.user_id == user_id, Baseline.is_active.is_(True))
            .order_by(Baseline.created_at.desc())
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_user(db: Session, user_id: str) -> List[Baseline]:
        stmt = (
            select(Baseline)
            .where(Baseline.user_id == user_id)
            .order_by(Baseline.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(
        db: Session, baseline_id: int, baseline_update: BaselineUpdate
    ) -> Optional[Baseline]:
        baseline = db.get(Baseline, baseline_id)
        if not baseline:
            return None

        update_data = baseline_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(baseline, field, value)

        db.flush()
        db.refresh(baseline)
        return baseline
