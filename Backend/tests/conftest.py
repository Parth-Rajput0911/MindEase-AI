"""
Pytest configuration and isolated test database fixtures for MindEase-AI.
Creates a dedicated isolated SQLite test database per test session/function.
"""

import os
import sys
from typing import Generator
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure workspace root and Backend/ are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from Backend.database import Base, configure_sqlite_connection, create_tables_direct, get_db
from Backend.main import app
from Backend.models import User
from Backend.repositories import UserRepository
from Backend.schemas import UserCreate


@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    """
    Creates an isolated SQLite test database file inside a temporary directory.
    Guarantees zero interference with development databases.
    """
    temp_dir = tmp_path_factory.mktemp("db_test")
    test_db_path = temp_dir / "test_mindease.db"
    database_url = f"sqlite:///{test_db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    event.listen(engine, "connect", configure_sqlite_connection)

    # Initialize all database tables using create_all (test-only, never touches production DB)
    create_tables_direct(engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db(test_engine) -> Generator[Session, None, None]:
    """
    Provides an isolated database session rolled back or cleaned up per test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    TestClient with overridden database dependency bound to the test session.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db: Session) -> User:
    """Creates a sample user for tests requiring an existing account."""
    user_in = UserCreate(
        email="test.tester@mindease.ai",
        username="test_tester",
        full_name="Test Patient",
        password="secure_password_test",
        emergency_contact_name="Emergency Ally",
        emergency_contact_phone="+1-555-0100",
        emergency_contact_email="ally@mindease.ai",
    )
    return UserRepository.create(db, user_in)
