"""Integration tests run against a real, freshly migrated database. They run only with
INTEGRATION_TESTS set (see scripts/integration.sh); plain `pytest` skips them."""

import asyncio
import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from testee_common.db.clean_start import start_clean, tables_left_empty

if not os.getenv("INTEGRATION_TESTS"):
    collect_ignore_glob = ["test_*.py", "*/test_*.py"]


@pytest.fixture(scope="session", autouse=True)
def database():
    """Creates the test database from scratch, runs every migration, and drops it afterwards;
    gives the tables the migrations left empty, those the tests fill."""
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(
        url.set(drivername="postgresql+psycopg", database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    command.upgrade(Config("alembic.ini"), "head")

    yield tables_left_empty(os.environ["DATABASE_URL"])

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))

    admin.dispose()


@pytest.fixture(autouse=True)
def clean_start(database):
    """Every test starts clean: the tables the tests fill emptied and the tests' Redis database
    flushed, whatever an earlier test left."""
    start_clean(os.environ["DATABASE_URL"], database, os.environ["REDIS_URL"])


@pytest.fixture
def run():
    """Runs a coroutine on a fresh event loop; the pool and the Redis client are dropped after,
    as their connections belong to that loop."""
    from billing.core.db import engine
    from billing.integrations.redis import get_redis

    def run(coroutine):
        async def wrapped():
            try:
                return await coroutine
            finally:
                await engine.dispose()
                get_redis.cache_clear()

        return asyncio.run(wrapped())

    return run


@pytest.fixture
def paddle_calls(monkeypatch):
    """Paddle's API, faked: what was charged and cancelled. A subscription whose id starts
    with sub_ended has ended in Paddle (cancelling it again is refused); one starting with
    sub_declined has a declined card (sub_declined_hard, for good); one starting with
    sub_timeout times out; Paddle fails to
    cancel one starting with sub_down."""
    import httpx

    from billing.config import settings
    from billing.integrations import paddle

    calls = []

    async def charge(subscription_id, price):
        """Records what it charged: the fixed top-up's key and its price."""
        amount = price["unit_price"]
        calls.append(
            (
                "charge",
                subscription_id,
                price["custom_data"]["top_up"],
                amount["amount"],
                amount["currency_code"],
            )
        )

        if subscription_id.startswith("sub_declined"):
            request = httpx.Request("POST", "https://paddle.test")
            response = httpx.Response(400, request=request)

            raise httpx.HTTPStatusError("declined", request=request, response=response)

        if subscription_id.startswith("sub_timeout"):
            raise httpx.ReadTimeout("timed out")

    async def charge_error(subscription_id, since, timeout):
        """Why the card declined: one starting with sub_declined_hard was refused for fraud, a
        decline that can't pass later; the others give no reason."""
        return "fraud" if subscription_id.startswith("sub_declined_hard") else None

    async def cancel(subscription_id):
        calls.append(("cancel", subscription_id))

        if subscription_id.startswith(("sub_ended", "sub_down")):
            request = httpx.Request("POST", "https://paddle.test")
            status = 400 if subscription_id.startswith("sub_ended") else 503
            response = httpx.Response(status, request=request)

            raise httpx.HTTPStatusError("not cancelled", request=request, response=response)

    async def subscription_status(subscription_id):
        return "canceled" if subscription_id.startswith("sub_ended") else "active"

    async def set_currency(subscription_id, currency):
        calls.append(("currency", subscription_id, currency))

    async def create_transaction(items, currency, custom_data):
        """The card's checkout: its id says the $0 price, the currency and whose card it saves."""
        return f"txn_{items[0]['price_id']}_{currency}_{custom_data['buyer_id']}"

    monkeypatch.setattr(paddle, "charge", charge)
    monkeypatch.setattr(paddle, "charge_error", charge_error)
    monkeypatch.setattr(paddle, "cancel", cancel)
    monkeypatch.setattr(paddle, "subscription_status", subscription_status)
    monkeypatch.setattr(paddle, "set_currency", set_currency)
    monkeypatch.setattr(paddle, "create_transaction", create_transaction)
    monkeypatch.setattr(settings, "paddle_api_key", "key")
    monkeypatch.setattr(settings, "paddle_price_auto_top_up", "pri_plan")
    monkeypatch.setattr(settings, "paddle_product_candidates", "pro_candidates")

    return calls


@pytest.fixture
def redis(monkeypatch):
    """Redis database 15 (see scripts/integration.sh) for the limits and the unpaid AI spend,
    with the limits read afresh."""
    from testee_common.redis import memory_cache

    from billing.integrations.redis import get_redis

    monkeypatch.setattr(memory_cache, "_entries", {})

    return get_redis


def charged(subscription_id, top_up="topup_50", currency="USD", subtotal="5000"):
    """Paddle's transaction.completed of an automatic top-up's charge: a price billing made under
    its product, buying `top_up`, paid `subtotal` in `currency`."""
    return {
        "id": f"txn_{uuid.uuid4().hex[:12]}",
        "subscription_id": subscription_id,
        "currency_code": currency,
        "custom_data": None,
        "items": [
            {
                "price": {
                    "id": "pri_made",
                    "product_id": "pro_candidates",
                    "custom_data": {"top_up": top_up},
                },
                "quantity": 1,
            }
        ],
        "details": {
            "totals": {"grand_total": subtotal},
            "line_items": [{"price_id": "pri_made", "totals": {"subtotal": subtotal}}],
        },
    }
