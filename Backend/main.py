"""
MindEase-AI Backend Entrypoint.
FastAPI web application exposing REST endpoints for sensor telemetry,
stress episodes, interventions, and notification events backed by SQLAlchemy 2.x.
"""

from contextlib import asynccontextmanager
import os
from typing import List, Optional
from dotenv import load_dotenv
# pyrefly: ignore[missing-import]
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
try:
    from groq import Groq
except ImportError:  # Keep the API usable when the optional AI dependency is not installed.
    Groq = None  # type: ignore[assignment,misc]

from .config import BASE_DIR, settings
from .database import create_tables_direct, get_db, init_db
from .repositories import (
    BaselineRepository,
    EpisodeRepository,
    InterventionRepository,
    NotificationEventRepository,
    SensorReadingRepository,
    UserRepository,
)
from .schemas import (
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
from emergency.emergency import (
    EmergencyContact,
    EmergencyDispatchPayload,
    EmergencyDispatchResult,
    EmergencyHotline,
    EmergencyService,
)

# Load environment variables from .env
load_dotenv()

# Create the optional AI client only when the SDK and an API key are available.
# This keeps the rest of the API (telemetry, episodes, tests) usable without AI credentials.
_groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=_groq_api_key) if Groq is not None and _groq_api_key else None


class ChatRequest(BaseModel):
    message: str

def get_wellness_response(message: str) -> str:
    """Calls Groq model to generate an empathetic mental wellness response."""
    prompt = (message or "").strip()
    if not prompt:
        return "I’m here to help. Please share how you’re feeling today."

    if groq_client is None:
        return (
            "I'm here with you. Try taking a comfortable, slow breath and notice "
            "five things you can see around you. AI responses are unavailable "
            "until the Groq SDK and GROQ_API_KEY are configured."
        )

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MindEase AI, a gentle, empathetic, and supportive mental wellness companion. "
                        "Provide comforting, human-like, and encouraging advice for managing stress and practicing mindfulness. "
                        "Do not issue medical diagnoses or clinical health advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return completion.choices[0].message.content
    except Exception:
        # Do not expose provider errors, request details, or configuration in user-facing text.
        return (
            "I'm listening. Try grounding yourself by noticing your feet on the floor "
            "and taking a comfortable, unforced breath. The AI service is temporarily unavailable."
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: register models on Base.metadata so SQLAlchemy is aware
    of all relationships. Table creation is left to Alembic migrations.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="MindEase-AI: Autonomous Stress & Anxiety Telemetry, Intervention, and Support Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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


# Frontend static files mounting and root redirect
_frontend_dir = BASE_DIR.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/app/")


# ============================================================================
# AI Chat Companion Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/chat",
    tags=["AI Chat Companion"],
)
def chat_with_mindease(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    reply = get_wellness_response(req.message)
    return {"reply": reply}


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
    """Create a user profile for the prototype. Authentication is not implemented yet."""
    if UserRepository.get_by_email(db, str(user_in.email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    if UserRepository.get_by_username(db, user_in.username):
        raise HTTPException(status_code=409, detail="Username is already registered")
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
    Record a notification event. Always initialized with is_simulated=True.
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
    Mark a notification as real and confirmed delivered by external provider.
    """
    updated = NotificationEventRepository.confirm_delivery(
        db, notification_id, confirmation
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Notification event not found")
    return updated


# ============================================================================
# Emergency Dispatch & Crisis Support Endpoints
# ============================================================================
@app.post(
    f"{settings.API_V1_PREFIX}/emergency/dispatch",
    response_model=EmergencyDispatchResult,
    status_code=status.HTTP_201_CREATED,
    tags=["Emergency Services"],
)
def trigger_emergency_dispatch(
    payload: EmergencyDispatchPayload,
    db: Session = Depends(get_db),
):
    """
    Trigger an emergency alert or acute panic assistance protocol.
    Notifies trusted contacts (simulated by default), creates audit
    records in database, and returns crisis hotlines and immediate coping steps.
    """
    try:
        return EmergencyService.dispatch(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Emergency dispatch failure: {str(exc)}")


@app.get(
    f"{settings.API_V1_PREFIX}/emergency/hotlines",
    response_model=List[EmergencyHotline],
    tags=["Emergency Services"],
)
def get_emergency_hotlines(
    region: Optional[str] = Query(None, description="Optional region filter (e.g. US, UK, EU, IN)"),
):
    """
    Retrieve verified 24/7 mental health crisis lines and emergency dispatch numbers.
    """
    return EmergencyService.get_hotlines(region=region)


@app.get(
    f"{settings.API_V1_PREFIX}/emergency/history/{{user_id}}",
    response_model=List[NotificationEventRead],
    tags=["Emergency Services"],
)
def get_user_emergency_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve recorded emergency alerts and panic dispatch events for a user.
    """
    return EmergencyService.get_user_emergency_history(db, user_id=user_id, limit=limit)