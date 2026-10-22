from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config.settings import settings
from app.constants.generation import CHECKPOINTER_POOL_SIZE


async def open_checkpointer() -> tuple[AsyncConnectionPool, AsyncPostgresSaver]:
    """LangGraph's checkpointer on a pool of its own. Its tables are set up by the migrations
    (migrations/env.py), not here."""
    pool = AsyncConnectionPool(
        settings.database_url,
        min_size=CHECKPOINTER_POOL_SIZE,
        max_size=CHECKPOINTER_POOL_SIZE,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await pool.open()

    return pool, AsyncPostgresSaver(pool)


async def delete_threads(thread_ids: list[str], checkpointer=None) -> None:
    """Deletes these generations' checkpoints through LangGraph, which owns their tables. Without
    a checkpointer (outside the worker), a short-lived one is opened."""
    if not thread_ids:
        return

    if checkpointer is not None:
        for thread_id in thread_ids:
            await checkpointer.adelete_thread(thread_id)

        return

    pool, own = await open_checkpointer()

    try:
        await delete_threads(thread_ids, own)
    finally:
        await pool.close()
