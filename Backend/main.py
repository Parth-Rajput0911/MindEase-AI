"""
MindEase-AI Backend Entrypoint.
FastAPI web application exposing REST endpoints for sensor telemetry,
stress episodes, interventions, and notification events backed by SQLAlchemy 2.x.
"""

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from Backend.config import settings
from Backend.database import create_tables_direct, get_db, init_db
from Backend.repositories import (
    BaselineRepository,
    EpisodeRepository,
    InterventionRepository,
    NotificationEventRepository,
    SensorReadingRepository,
    UserRepository,
)
from Backend.schemas import (
    BaselineCreate,
    BaselineRead,
    EpisodeCreate,
    EpisodeRead,
    InterventionCreate,
    InterventionRead,
    NotificationDeliveryConfirmation,
    NotificationEventCreate,
    NotificationEventRead,
    SensorReadingBatchCreate,
    SensorReadingCreate,
    SensorReadingRead,
    UserCreate,
    UserRead,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: register models on Base.metadata so SQLAlchemy is aware
    of all relationships.  Table creation is left to Alembic migrations.
    `create_tables_direct()` is intentionally NOT called here to avoid
    creating tables that bypass migration version tracking.
    """
    init_db()  # registers models only; does NOT call create_all()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="MindEase-AI: Autonomous Stress & Anxiety Telemetry, Intervention, and Support Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating API and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
    }


# ============================================================================
# User Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if UserRepository.get_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if UserRepository.get_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    return UserRepository.create(db, user_in)


@app.get(
    f"{settings.API_V1_PREFIX}/users/{{user_id}}",
    response_model=UserRead,
    tags=["Users"],
)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================================
# Sensor Telemetry Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/sensors/readings",
    response_model=SensorReadingRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensor Telemetry"],
)
def ingest_sensor_reading(
    reading_in: SensorReadingCreate, db: Session = Depends(get_db)
):
    """
    Ingest a single sensor reading.
    Missing sensor channels are saved as NULL rather than 0.
    """
    return SensorReadingRepository.create(db, reading_in)


@app.post(
    f"{settings.API_V1_PREFIX}/sensors/batch",
    response_model=List[SensorReadingRead],
    status_code=status.HTTP_201_CREATED,
    tags=["Sensor Telemetry"],
)
def ingest_sensor_batch(
    batch_in: SensorReadingBatchCreate, db: Session = Depends(get_db)
):
    """
    Ingest a batch of telemetry samples.
    Missing metrics are preserved as NULL.
    """
    return SensorReadingRepository.bulk_create(db, batch_in)


@app.get(
    f"{settings.API_V1_PREFIX}/sensors/readings/{{user_id}}",
    response_model=List[SensorReadingRead],
    tags=["Sensor Telemetry"],
)
def get_sensor_readings(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return SensorReadingRepository.get_by_user(db, user_id=user_id, limit=limit)


# ============================================================================
# Baselines Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/baselines",
    response_model=BaselineRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Baselines"],
)
def create_baseline(baseline_in: BaselineCreate, db: Session = Depends(get_db)):
    return BaselineRepository.create(db, baseline_in)


@app.get(
    f"{settings.API_V1_PREFIX}/baselines/{{user_id}}/active",
    response_model=Optional[BaselineRead],
    tags=["Baselines"],
)
def get_active_baseline(user_id: str, db: Session = Depends(get_db)):
    baseline = BaselineRepository.get_active(db, user_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="No active baseline found")
    return baseline


# ============================================================================
# Episode Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/episodes",
    response_model=EpisodeRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Episodes"],
)
def log_episode(episode_in: EpisodeCreate, db: Session = Depends(get_db)):
    return EpisodeRepository.create(db, episode_in)


@app.get(
    f"{settings.API_V1_PREFIX}/episodes/{{user_id}}",
    response_model=List[EpisodeRead],
    tags=["Episodes"],
)
def list_episodes(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return EpisodeRepository.get_by_user(db, user_id=user_id, status=status, limit=limit)


# ============================================================================
# Intervention Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/interventions",
    response_model=InterventionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Interventions"],
)
def log_intervention(
    intervention_in: InterventionCreate, db: Session = Depends(get_db)
):
    return InterventionRepository.create(db, intervention_in)


@app.get(
    f"{settings.API_V1_PREFIX}/interventions/{{user_id}}",
    response_model=List[InterventionRead],
    tags=["Interventions"],
)
def list_interventions(
    user_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return InterventionRepository.get_by_user(db, user_id=user_id, status=status)


# ============================================================================
# Notification Event Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/notifications",
    response_model=NotificationEventRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Notifications"],
)
def record_notification(
    notification_in: NotificationEventCreate, db: Session = Depends(get_db)
):
    """
    Record a notification event. Always initialized with is_simulated=True (Req #12).
    """
    return NotificationEventRepository.create(db, notification_in)


@app.get(
    f"{settings.API_V1_PREFIX}/notifications/{{user_id}}",
    response_model=List[NotificationEventRead],
    tags=["Notifications"],
)
def list_notifications(
    user_id: str,
    simulated_only: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return NotificationEventRepository.get_by_user(
        db, user_id=user_id, simulated_only=simulated_only
    )


@app.post(
    f"{settings.API_V1_PREFIX}/notifications/{{notification_id}}/confirm-delivery",
    response_model=NotificationEventRead,
    tags=["Notifications"],
)
def confirm_notification_delivery(
    notification_id: int,
    confirmation: NotificationDeliveryConfirmation,
    db: Session = Depends(get_db),
):
    """
    Mark a notification as real and confirmed delivered by external provider (Req #12).
    """
    updated = NotificationEventRepository.confirm_delivery(
        db, notification_id, confirmation
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Notification event not found")
    return updated
