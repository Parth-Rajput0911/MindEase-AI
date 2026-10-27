"""
Repository for Episode database operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.database import now_utc
from Backend.models.episode import Episode
from Backend.schemas.episode import EpisodeCreate, EpisodeUpdate


class EpisodeRepository:
    @staticmethod
    def create(db: Session, episode_in: EpisodeCreate) -> Episode:
        episode = Episode(
            user_id=episode_in.user_id,
            start_time=episode_in.start_time,
            end_time=episode_in.end_time,
            peak_severity=episode_in.peak_severity,
            episode_type=episode_in.episode_type,
            status=episode_in.status,
            trigger_description=episode_in.trigger_description,
            resolution_notes=episode_in.resolution_notes,
            baseline_id=episode_in.baseline_id,
        )
        db.add(episode)
        db.flush()
        db.refresh(episode)
        return episode

    @staticmethod
    def get_by_id(db: Session, episode_id: int) -> Optional[Episode]:
        return db.get(Episode, episode_id)

    @staticmethod
    def get_by_user(
        db: Session, user_id: str, status: Optional[str] = None, limit: int = 50
    ) -> List[Episode]:
        stmt = (
            select(Episode)
            .where(Episode.user_id == user_id)
            .order_by(Episode.start_time.desc())
        )
        if status:
            stmt = stmt.where(Episode.status == status)
        stmt = stmt.limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(
        db: Session, episode_id: int, episode_update: EpisodeUpdate
    ) -> Optional[Episode]:
        episode = db.get(Episode, episode_id)
        if not episode:
            return None

        update_data = episode_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(episode, field, value)

        db.flush()
        db.refresh(episode)
        return episode

    @staticmethod
    def resolve(
        db: Session, episode_id: int, notes: Optional[str] = None
    ) -> Optional[Episode]:
        episode = db.get(Episode, episode_id)
        if not episode:
            return None

        episode.status = "resolved"
        episode.end_time = now_utc()
        if notes:
            episode.resolution_notes = notes

        db.flush()
        db.refresh(episode)
        return episode
