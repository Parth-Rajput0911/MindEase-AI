"""
Pydantic v2 schemas for Therapeutic Interventions.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InterventionBase(BaseModel):
    intervention_type: str = Field(..., max_length=50)
    status: str = Field(default="suggested", max_length=50)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    user_feedback_rating: Optional[int] = Field(None, ge=1, le=5)
    user_notes: Optional[str] = None
    episode_id: Optional[int] = None


class InterventionCreate(InterventionBase):
    user_id: str


class InterventionUpdate(BaseModel):
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    user_feedback_rating: Optional[int] = Field(None, ge=1, le=5)
    user_notes: Optional[str] = None


class InterventionRead(InterventionBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
