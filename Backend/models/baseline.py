"""
Baseline model for MindEase-AI.
Stores calibrated physiological baselines per user across specific observation windows.
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Backend.database import Base, UTCDateTime, now_utc

if TYPE_CHECKING:
    from Backend.models.episode import Episode
    from Backend.models.user import User


class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    baseline_heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_eda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_skin_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_respiratory_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # Calibration window in UTC
    window_start: Mapped[UTCDateTime] = mapped_column(UTCDateTime, nullable=False)
    window_end: Mapped[UTCDateTime] = mapped_column(UTCDateTime, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calibration_status: Mapped[str] = mapped_column(
        String(50), default="calibrated", nullable=False
    )

    created_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        nullable=False,
    )
    updated_at: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime,
        default=now_utc,
        onupdate=now_utc,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="baselines")
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode", back_populates="baseline"
    )

    def __repr__(self) -> str:
        return (
            f"<Baseline(id={self.id}, user_id='{self.user_id}', "
            f"status='{self.calibration_status}', active={self.is_active})>"
        )
