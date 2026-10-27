import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Ensure workspace root and Backend/ are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from Backend.config import settings
from Backend.models import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Resolve the effective database URL.
# Priority (highest → lowest):
#   1. URL set programmatically via alembic_cfg.set_main_option() in tests / CI.
#   2. DATABASE_URL from settings (absolute path, always used when running
#      interactively from the command line so CWD doesn't affect resolution).
#   3. The static placeholder in alembic.ini (never used in practice).
_PLACEHOLDER_URLS = {
    None,
    "",
    "driver://user:pass@localhost/dbname",
    "sqlite:///./mindease.db",         # Backend/alembic.ini default
    "sqlite:///./Backend/mindease.db", # root alembic.ini default
}

_ini_url = config.get_main_option("sqlalchemy.url")
if _ini_url in _PLACEHOLDER_URLS:
    # No explicit override from caller — use the absolute settings URL so that
    # interactive `alembic upgrade head` works regardless of working directory.
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Essential for SQLite column/constraint changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Essential for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
