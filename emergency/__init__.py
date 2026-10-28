"""
MindEase-AI Emergency Service Package.
Provides emergency dispatch, contact alerts, hotline directories,
and escalation procedures during acute panic and stress episodes.
"""

from .emergency import (
    EmergencyService,
    EmergencyContact,
    EmergencyDispatchPayload,
    EmergencyDispatchResult,
    EmergencyHotline,
    EMERGENCY_HOTLINES,
)

__all__ = [
    "EmergencyService",
    "EmergencyContact",
    "EmergencyDispatchPayload",
    "EmergencyDispatchResult",
    "EmergencyHotline",
    "EMERGENCY_HOTLINES",
]
