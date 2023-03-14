import os
from logging import config as logging_config

import sqlalchemy
from scheduler import config as scheduler_config
from scheduler.db import models
from scheduler.db.service import get_test_db_url

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
if not os.getenv("USE_TEST_DB"):
    context.config.set_main_option("sqlalchemy.url", scheduler_config.DB_URL)
else:
    context.config.set_main_option(
        "sqlalchemy.url", get_test_db_url(scheduler_config.DB_URL)
    )

# Interpret the config file for Python logging.
# This line sets up loggers basically.
logging_config.fileConfig(context.config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = sqlalchemy.engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=sqlalchemy.pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
