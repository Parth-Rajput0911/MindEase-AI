"""
Database configuration, session management, and connection utilities for MindEase-AI.
Uses SQLAlchemy 2.x with consistent UTC timestamping and SQLite optimization.
"""

from datetime import datetime, timezone
from typing import Generator
import sqlite3

from sqlalchemy import DateTime, Engine, TypeDecorator, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from Backend.config import settings


def now_utc() -> datetime:
    """Return the current time in UTC with timezone information."""
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """
    SQLAlchemy type decorator ensuring all datetimes are stored
    consistently in UTC and returned with explicit UTC timezone info.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            # Assume naive datetime is in UTC
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Base(DeclarativeBase):
    """SQLAlchemy 2.x Declarative Base."""
    pass


# SQLite connection tuning (enable foreign keys and WAL journal mode)
@event.listens_for(Engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def create_db_engine(database_url: str = settings.DATABASE_URL):
    """Create a configured SQLAlchemy engine."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        connect_args=connect_args,
        echo=settings.DEBUG and settings.APP_ENV == "development",
        future=True,
    )


engine = create_db_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for FastAPI and standalone services.
    Ensures safe session commit/rollback and automatic cleanup.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Imports all models so their metadata is registered on Base.
    This is safe to call at any time (startup, test setup, alembic env)
    and does NOT create any tables itself.

    Table creation must be done either:
      - Via Alembic (`alembic upgrade head`) in production/development.
      - Via `create_tables_direct(engine)` in isolated test environments.
    """
    from Backend import models  # noqa: F401  – registers models on Base.metadata


def create_tables_direct(target_engine=None):
    """
    Create all tables directly using SQLAlchemy's create_all().

    ONLY intended for isolated test databases and CI environments
    where Alembic migrations are not used.  Do NOT call this against
    a production or development database that is managed by Alembic –
    it will bypass migration tracking and cause `alembic upgrade head`
    to fail with "table already exists".
    """
    from Backend import models  # noqa: F401  – registers models on Base.metadata

    db_engine = target_engine or engine
    Base.metadata.create_all(bind=db_engine)
