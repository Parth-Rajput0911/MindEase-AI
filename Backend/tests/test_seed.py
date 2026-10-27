"""
Unit tests for database seed script and sample data integrity.
"""

from sqlalchemy.orm import Session

from Backend.models import (
    Baseline,
    Episode,
    Intervention,
    NotificationEvent,
    SensorReading,
    User,
)
from Backend.scripts.seed_db import seed_database


def test_seed_database_execution_and_idempotence(db: Session):
    """
    Ensure the seed script populates all tables with synthetic demo data,
    and runs idempotently when invoked repeatedly.
    """
    # First execution
    demo_user = seed_database(db)
    assert demo_user is not None
    assert demo_user.email == "demo.synthetic@mindease.ai"

    # Verify tables populated
    readings = db.query(SensorReading).filter_by(user_id=demo_user.id).all()
    assert len(readings) == 5

    # Verify that at least one reading has NULL heart_rate (Req #3)
    null_hr_readings = [r for r in readings if r.heart_rate is None]
    assert len(null_hr_readings) >= 1

    # Verify that at least one reading has NULL eda (Req #3)
    null_eda_readings = [r for r in readings if r.eda is None]
    assert len(null_eda_readings) >= 1

    # Verify baseline
    baselines = db.query(Baseline).filter_by(user_id=demo_user.id).all()
    assert len(baselines) >= 1

    # Verify episode
    episodes = db.query(Episode).filter_by(user_id=demo_user.id).all()
    assert len(episodes) >= 1

    # Verify intervention
    interventions = db.query(Intervention).filter_by(user_id=demo_user.id).all()
    assert len(interventions) >= 1

    # Verify notification events marked is_simulated=True (Req #12)
    notifications = db.query(NotificationEvent).filter_by(user_id=demo_user.id).all()
    assert len(notifications) >= 1
    for n in notifications:
        assert n.is_simulated is True
        assert n.status == "simulated"

    # Second execution (Idempotence test)
    demo_user_2 = seed_database(db)
    assert demo_user_2 is not None
    assert demo_user_2.email == "demo.synthetic@mindease.ai"
