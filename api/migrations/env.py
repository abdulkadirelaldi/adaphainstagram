"""Alembic ortamı — async.

Migration'lar asyncpg sürücüsüyle çalışır (sistemin geri kalanıyla aynı sürücü;
ayrı bir sync sürücü/bağımlılık gerekmez). URL `.env`'den `api.config` üzerinden
okunur, `alembic.ini`'ye gömülmez.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from api.config import get_settings
from api.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Adresi ayarlardan enjekte et — tek sır kaynağı .env.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Autogenerate ve `alembic check` bu metadata'ya bakar.
target_metadata = Base.metadata


def _configure(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Sunucu varsayılanı değişikliklerini de diff'e dahil et: outreach.status
        # 'draft' varsayılanı gibi kararların migration ile eşleştiğini doğrular.
        compare_type=True,
        compare_server_default=True,
    )


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
