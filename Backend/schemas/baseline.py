"""
Pydantic v2 schemas for Physiological Baselines.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BaselineBase(BaseModel):
    baseline_heart_rate: Optional[float] = Field(None, description="Resting heart rate in BPM")
    baseline_eda: Optional[float] = Field(None, description="Baseline electrodermal activity in uS")
    baseline_skin_temp: Optional[float] = Field(None, description="Baseline skin temperature in Celsius")
    baseline_respiratory_rate: Optional[float] = Field(None, description="Baseline respiration rate")
    window_start: datetime
    window_end: datetime
    is_active: bool = True
    calibration_status: str = Field(default="calibrated", max_length=50)


class BaselineCreate(BaselineBase):
    user_id: str


class BaselineUpdate(BaseModel):
    baseline_heart_rate: Optional[float] = None
    baseline_eda: Optional[float] = None
    baseline_skin_temp: Optional[float] = None
    baseline_respiratory_rate: Optional[float] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    is_active: Optional[bool] = None
    calibration_status: Optional[str] = None


class BaselineRead(BaselineBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
