from logging.config import fileConfig
from sqlalchemy import create_engine, pool, text
from alembic import context

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.database import Base

# Import all models so they are registered with Base.metadata
import app.models.models  # noqa: F401

# Alembic Config object (do NOT call set_main_option — configparser
# chokes on special characters like % or // in URLs)
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Build a synchronous psycopg2 URL from the asyncpg DATABASE_URL.
_sync_url = (
    settings.database_url
    .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    .replace("postgresql://", "postgresql+psycopg2://")
)


def include_object(object, name, type_, reflected, compare_to):
    """Only include objects in the qbe_demo schema; ignore all Supabase internals."""
    if type_ == "table":
        return getattr(object, "schema", None) == settings.db_schema
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        version_table_schema=settings.db_schema,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        _sync_url,
        poolclass=pool.NullPool,
        connect_args={"sslmode": "require"},
    )

    with connectable.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            version_table_schema=settings.db_schema,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

