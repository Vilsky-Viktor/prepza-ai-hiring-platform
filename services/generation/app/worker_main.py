from contextlib import asynccontextmanager

from fastapi import FastAPI
from prepza_common.ai.trace_prices import sync_model_prices
from prepza_common.http.health import health_router
from prepza_common.http.shutdown import close_shared
from prepza_common.observability.logging import RequestLogMiddleware, configure_logging
from prepza_common.observability.sentry import init_sentry

from app.integrations.redis import get_redis
from app.routers import jobs, schedules
from app.services.graph import build_graph
from app.storage.checkpointer import open_checkpointer
from app.storage.db import engine

configure_logging()
init_sentry("generation-worker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """The worker: Cloud Tasks runs jobs and Cloud Scheduler runs schedules through it."""
    app.state.pool, app.state.checkpointer = await open_checkpointer()
    app.state.graph = build_graph(app.state.checkpointer)
    await sync_model_prices()

    yield

    await app.state.pool.close()
    await close_shared(engine, get_redis())


# Only Google calls it, so there's no API description to serve.
app = FastAPI(title="generation-worker", lifespan=lifespan, openapi_url=None)
app.add_middleware(RequestLogMiddleware)
app.include_router(jobs.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
