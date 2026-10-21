from prepza_common.constants import (
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE_SECONDS,
    DB_POOL_SIZE,
    DELETE_BATCH,
    IDLE_IN_TRANSACTION_TIMEOUT,
    MIGRATION_LOCK_TIMEOUT,
    MIGRATION_STATEMENT_TIMEOUT,
    STATEMENT_TIMEOUT,
)
from sqlalchemy import Engine, create_engine, delete, inspect, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def one_of(column: str, values) -> str:
    """A CHECK's condition that `column` holds one of `values` (an enum's members, a tuple): the
    database refuses any other, so the closed set lives in one place, the code."""
    listed = ", ".join("'" + str(value).replace("'", "''") + "'" for value in values)

    return f"{column} IN ({listed})"


def sqlalchemy_url(database_url: str) -> str:
    """A service's postgresql:// URL, with the psycopg driver SQLAlchemy connects through."""
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)


def database(
    url: str, pool_size: int = DB_POOL_SIZE, max_overflow: int = DB_MAX_OVERFLOW
) -> tuple[AsyncEngine, async_sessionmaker]:
    """The engine and session factory for a service's database; a service with few, short queries
    takes a smaller pool, to stay within the database's connection budget. A transaction left
    idle past IDLE_IN_TRANSACTION_TIMEOUT, and a statement running past STATEMENT_TIMEOUT, are
    ended by Postgres. A database error carries no query values (emails, names, answers) into
    the logs or Sentry."""
    engine = create_async_engine(
        sqlalchemy_url(url),
        hide_parameters=True,
        pool_recycle=DB_POOL_RECYCLE_SECONDS,
        pool_size=pool_size,
        max_overflow=max_overflow,
        connect_args={
            "options": (
                f"-c idle_in_transaction_session_timeout={IDLE_IN_TRANSACTION_TIMEOUT} "
                f"-c statement_timeout={STATEMENT_TIMEOUT}"
            )
        },
    )

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def migration_engine(database_url: str) -> Engine:
    """The engine a service's migrations (Alembic's env.py) run on: a statement waiting longer
    than MIGRATION_LOCK_TIMEOUT for a lock fails rather than block its table, and one running
    longer than MIGRATION_STATEMENT_TIMEOUT is stopped."""
    options = (
        f"-c lock_timeout={MIGRATION_LOCK_TIMEOUT} "
        f"-c statement_timeout={MIGRATION_STATEMENT_TIMEOUT}"
    )

    return create_engine(sqlalchemy_url(database_url), connect_args={"options": options})


async def delete_in_batches(sessionmaker, model, *conditions, batch: int = DELETE_BATCH) -> int:
    """Deletes `model`'s rows matching `conditions`, `batch` at a time, each batch committed on
    its own, and returns how many went. For old rows (retention): a run cut off midway keeps what
    it deleted, and the next run goes on."""
    (key,) = inspect(model).primary_key
    total = 0

    while True:
        chosen = select(key).where(*conditions).limit(batch)

        async with sessionmaker() as session:
            result = await session.execute(delete(model).where(key.in_(chosen)))
            await session.commit()

        total += result.rowcount

        if result.rowcount < batch:
            return total


async def ping(engine: AsyncEngine) -> None:
    """Raises if the database doesn't answer."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
