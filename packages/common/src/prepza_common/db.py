from prepza_common.constants import (
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE_SECONDS,
    DB_POOL_SIZE,
    IDLE_IN_TRANSACTION_TIMEOUT,
    MIGRATION_LOCK_TIMEOUT,
)
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def sqlalchemy_url(database_url: str) -> str:
    """A service's postgresql:// URL, with the psycopg driver SQLAlchemy connects through."""
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)


def database(
    url: str, pool_size: int = DB_POOL_SIZE, max_overflow: int = DB_MAX_OVERFLOW
) -> tuple[AsyncEngine, async_sessionmaker]:
    """The engine and session factory for a service's database; a service with few, short queries
    takes a smaller pool, to stay within the database's connection budget. A transaction left
    idle past IDLE_IN_TRANSACTION_TIMEOUT is ended by Postgres."""
    engine = create_async_engine(
        sqlalchemy_url(url),
        pool_recycle=DB_POOL_RECYCLE_SECONDS,
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args={
            "options": f"-c idle_in_transaction_session_timeout={IDLE_IN_TRANSACTION_TIMEOUT}"
        },
    )

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def migration_engine(database_url: str) -> Engine:
    """The engine a service's migrations (Alembic's env.py) run on: a statement waiting longer
    than MIGRATION_LOCK_TIMEOUT for a lock fails rather than block its table."""
    options = f"-c lock_timeout={MIGRATION_LOCK_TIMEOUT}"

    return create_engine(sqlalchemy_url(database_url), connect_args={"options": options})


async def ping(engine: AsyncEngine) -> None:
    """Raises if the database doesn't answer."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
