"""
Pydantic v2 schemas for Stress & Anxiety Episodes.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EpisodeBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_severity: float = Field(..., ge=0.0, le=10.0, description="Severity score 0 to 10")
    episode_type: str = Field(default="stress", max_length=50)
    status: str = Field(default="ongoing", max_length=50)
    trigger_description: Optional[str] = None
    resolution_notes: Optional[str] = None
    baseline_id: Optional[int] = None


class EpisodeCreate(EpisodeBase):
    user_id: str


class EpisodeUpdate(BaseModel):
    end_time: Optional[datetime] = None
    peak_severity: Optional[float] = Field(None, ge=0.0, le=10.0)
    episode_type: Optional[str] = None
    status: Optional[str] = None
    trigger_description: Optional[str] = None
    resolution_notes: Optional[str] = None
    baseline_id: Optional[int] = None


class EpisodeRead(EpisodeBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
