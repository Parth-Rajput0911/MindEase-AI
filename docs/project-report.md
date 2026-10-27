# MindEase-AI Technical Report: Database Layer Architecture

## Executive Summary
This report documents the architectural design, schema definitions, and implementation patterns for the database layer of the **MindEase-AI** platform. MindEase-AI monitors real-time physiological signals (heart rate, electrodermal activity, skin temperature, respiratory rate), establishes baseline states, detects stress/anxiety episodes, triggers adaptive interventions, and manages emergency notification events.

---

## Technical Stack & Design Choices

1. **SQLAlchemy 2.0 Modern Standards**:
   - Built on `DeclarativeBase` with type-annotated `Mapped[...]` and `mapped_column(...)`.
   - Uses `relationship(...)` with explicit cascade policies (`all, delete-orphan` from `User` to child entities; `SET NULL` for baseline/episode references).
   - Foreign key integrity is strictly enforced on SQLite connections via `PRAGMA foreign_keys = ON;`.
   - Concurrency is optimized with SQLite Write-Ahead Logging (`PRAGMA journal_mode = WAL;`).

2. **Telemetry Sparse Data & NULL Policy**:
   - Wearable sensors continuously experience channel disconnects, motion artifacts, or electrode dropouts (e.g., optical PPG failing due to ambient light or skin contact loss while galvanic skin response remains active).
   - **Crucial Rule**: Missing telemetry metrics are preserved as SQL `NULL` and **never** coerced to `0` or `0.0`. A zero heart rate represents cardiac arrest, not a dropped packet.
   - Pydantic ingestion schemas declare `Optional[float] = None` with default `None`.

3. **UTC Datetime Normalization**:
   - MindEase-AI uses a custom `UTCDateTime` TypeDecorator on top of SQLAlchemy's `DateTime(timezone=True)`.
   - Incoming timestamps (whether naive, UTC, or containing local timezone offsets) are bound and stored strictly in UTC.
   - Retrieved datetime objects always carry `tzinfo=timezone.utc`.

4. **Notification Simulation Safety Guarantee**:
   - Mental health platforms communicating panic or emergency dispatch alerts must maintain strict audit separation between simulated local development events and actual delivery.
   - All `notification_events` records are assigned `is_simulated = True` and `status = "simulated"` by default.
   - Only a verified provider webhook/confirmation token can transition records to `is_simulated = False` and `status = "delivered"`.

5. **Alembic Database Migrations**:
   - Alembic is configured under `Backend/alembic` with `render_as_batch=True` to support SQLite table and constraint alterations.
   - Initial migration `d07cb50af659_initial_schema.py` provides verified forward (`upgrade head`) and rollback (`downgrade base`) execution.

6. **Automated Testing Strategy**:
   - The test suite executes in dedicated, temporary SQLite databases via `pytest` fixtures (`tmp_path`).
   - 24 automated tests cover model relationships, constraint enforcement, NULL metric preservation, UTC timestamp conversion, notification simulation rules, repository CRUD operations, seed idempotence, migration rollback, and FastAPI endpoints.
