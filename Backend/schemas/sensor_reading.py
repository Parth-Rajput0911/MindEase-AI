"""
Pydantic v2 schemas for Sensor Readings.
Explicitly supports missing sensor metrics as NULL/None, avoiding zero-coercion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorReadingBase(BaseModel):
    timestamp: Optional[datetime] = None
    # All sensor metrics must default to None, never coerced to 0 or 0.0
    heart_rate: Optional[float] = Field(
        default=None,
        description="Heart rate in BPM (NULL if sensor offline)",
    )
    eda: Optional[float] = Field(
        default=None,
        description="Electrodermal activity in uS (NULL if channel disconnected)",
    )
    skin_temperature: Optional[float] = Field(
        default=None,
        description="Skin temperature in Celsius (NULL if disconnected)",
    )
    blood_oxygen: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="SpO2 percentage (NULL if disconnected)",
    )
    respiratory_rate: Optional[float] = Field(
        default=None,
        description="Breaths per minute (NULL if disconnected)",
    )
    step_count: Optional[int] = Field(
        default=None,
        description="Step count interval (NULL if not tracked)",
    )
    device_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Source wearable or simulator device ID",
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional raw payload or vendor-specific telemetry",
    )


class SensorReadingCreate(SensorReadingBase):
    user_id: str


class SensorReadingBatchCreate(BaseModel):
    user_id: str
    readings: List[SensorReadingBase]


class SensorReadingRead(SensorReadingBase):
    id: int
    user_id: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
