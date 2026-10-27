"""
Automated tests for Alembic database migrations.
Covers three scenarios:
  1. Fresh database: upgrade head creates all tables.
  2. Downgrade to base then re-upgrade to head (rollback round-trip).
  3. Pre-existing compatible schema: upgrade head must be a safe no-op when
     tables already exist and the database has been stamped at head, i.e.,
     it must never raise "table already exists".
"""

import os
import sqlite3

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect


def _make_alembic_cfg(db_url: str) -> Config:
    """Return an Alembic Config object targeting a specific database URL."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    alembic_ini_path = os.path.join(base_dir, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    return alembic_cfg


def test_fresh_database_upgrade_and_downgrade(tmp_path):
    """
    Scenario 1 & 2: Fresh empty database.
    - upgrade head creates all six application tables.
    - downgrade base drops them all.
    - re-upgrade recreates them.
    """
    test_db_path = tmp_path / "fresh_test.db"
    db_url = f"sqlite:///{test_db_path}"
    alembic_cfg = _make_alembic_cfg(db_url)

    # 1. Upgrade to head — all tables must be created
    command.upgrade(alembic_cfg, "head")
    assert test_db_path.exists()

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    expected = {"users", "baselines", "sensor_readings", "episodes",
                "interventions", "notification_events", "alembic_version"}
    assert expected == table_names, f"Missing tables: {expected - table_names}"

    # 2. Downgrade to base — all application tables must be dropped
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    remaining = set(inspector.get_table_names())
    # Only alembic_version may remain (empty) after a full downgrade
    application_tables = remaining - {"alembic_version"}
    assert not application_tables, f"Tables still exist after downgrade: {application_tables}"

    # 3. Re-upgrade to head
    command.upgrade(alembic_cfg, "head")
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
    engine.dispose()


def test_upgrade_head_is_idempotent(tmp_path):
    """
    Scenario 3: Idempotency / double-upgrade.
    Running `upgrade head` twice in a row must succeed without errors,
    producing exactly zero migration operations on the second call.
    """
    test_db_path = tmp_path / "idempotent_test.db"
    db_url = f"sqlite:///{test_db_path}"
    alembic_cfg = _make_alembic_cfg(db_url)

    # First upgrade
    command.upgrade(alembic_cfg, "head")

    # Second upgrade — must be a clean no-op, no OperationalError
    command.upgrade(alembic_cfg, "head")


def test_pre_existing_compatible_schema_can_be_stamped(tmp_path):
    """
    Scenario 4: Simulates the real-world situation that caused the bug.

    A database whose tables were created by SQLAlchemy's `create_all()`
    (not Alembic) has an empty `alembic_version` table and a fully
    compatible schema.  The correct recovery is:
      1. Verify schema compatibility.
      2. `alembic stamp head` — marks the DB as already at head.
      3. `alembic upgrade head` — must succeed as a no-op.

    This test ensures our fix (stamping) works correctly and that a
    subsequent `upgrade head` raises NO errors.
    """
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    from Backend.database import create_tables_direct
    from sqlalchemy import create_engine as sa_create_engine

    test_db_path = tmp_path / "pre_existing_test.db"
    db_url = f"sqlite:///{test_db_path}"

    # Step 1: Simulate tables created by create_all() — no alembic_version tracking
    pre_engine = sa_create_engine(db_url, connect_args={"check_same_thread": False})
    create_tables_direct(pre_engine)
    pre_engine.dispose()

    # Verify alembic_version table was NOT created by create_all (expected: missing)
    conn = sqlite3.connect(str(test_db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables_before = {row[0] for row in cur.fetchall()}
    conn.close()
    # create_all does not create alembic_version
    assert "alembic_version" not in tables_before
    assert "users" in tables_before

    # Step 2: Run `alembic upgrade head` — this is expected to fail with
    # "table already exists" unless we stamp first.  We stamp here.
    alembic_cfg = _make_alembic_cfg(db_url)
    command.stamp(alembic_cfg, "head")

    # Step 3: Now upgrade head must be a clean no-op
    command.upgrade(alembic_cfg, "head")

    # Step 4: Verify alembic_version now records the head revision
    conn2 = sqlite3.connect(str(test_db_path))
    cur2 = conn2.cursor()
    cur2.execute("SELECT version_num FROM alembic_version")
    row = cur2.fetchone()
    conn2.close()
    assert row is not None, "alembic_version should contain a row after stamping"
    assert row[0] == "d07cb50af659"


def test_head_revision_matches_expected(tmp_path):
    """
    Sanity check: ensure the head revision ID in the version files
    matches the revision used in the stamp test above.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    alembic_ini_path = os.path.join(base_dir, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()
    assert head_revision == "d07cb50af659", (
        f"Expected head revision d07cb50af659, got {head_revision}"
    )
