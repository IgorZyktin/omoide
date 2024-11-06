"""Entry point for alembic."""
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from omoide import const
from omoide.database import db_models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db_models.Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    db_url = os.getenv(const.ENV_DB_URL_ADMIN)

    if db_url is None:
        msg = f'You have to set admin url using {const.ENV_DB_URL_ADMIN!r} variable'
        raise RuntimeError(msg)

    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    db_url = os.getenv(const.ENV_DB_URL_ADMIN)

    if db_url is None:
        msg = f'You have to set admin url using {const.ENV_DB_URL_ADMIN!r} variable'
        raise RuntimeError(msg)

    config.set_main_option('sqlalchemy.url', db_url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
