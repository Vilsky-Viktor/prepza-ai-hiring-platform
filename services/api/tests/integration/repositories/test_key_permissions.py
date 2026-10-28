import asyncio
import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from api.core.db import Session
from api.repositories import keys
from tests.integration.repositories.test_action_log_events import logged
from tests.integration.transactions import transaction

READS = ["interviews:read", "candidates:read"]
EVERY_API_PERMISSION = [
    "interviews:read",
    "interviews:create",
    "candidates:read",
    "candidates:invite",
    "candidates:change",
    "candidates:delete",
    "credits:read",
]


def new_key(company, permissions):
    return transaction(
        keys.add, company, "Site", "pz_x", uuid.uuid4().hex * 2, "u1", None, permissions, 10
    )


def test_a_keys_permissions_are_only_narrowed(run):
    company = uuid.uuid4()

    async def scenario():
        made = await new_key(company, ["candidates:invite", *READS])
        narrowed = await transaction(keys.narrow, company, made.id, ["candidates:read"], "u2")
        widened = await transaction(keys.narrow, company, made.id, READS, "u2")
        elsewhere = await transaction(keys.narrow, uuid.uuid4(), made.id, ["candidates:read"], "u2")
        # Nothing taken away: nothing to log.
        same = await transaction(keys.narrow, company, made.id, ["candidates:read"], "u2")

        return (
            narrowed,
            widened,
            elsewhere,
            same,
            await transaction(keys.get, company, made.id),
            made,
        )

    narrowed, widened, elsewhere, same, stored, made = run(scenario())
    events = run(logged(company))

    assert narrowed.permissions == ["candidates:read"] == same.permissions
    assert widened is None and elsewhere is None
    assert stored.permissions == ["candidates:read"]
    # Made and narrowed, for the company's action log, with what was taken away and by whom.
    assert [(row["action"], row["user_id"], row["removed"]) for row in events] == [
        ("api_key_created", "u1", None),
        ("api_key_narrowed", "u2", ["candidates:invite", "interviews:read"]),
    ]
    assert (events[1]["target_kind"], events[1]["target_id"], events[1]["target_label"]) == (
        "api_key",
        str(made.id),
        "Site",
    )


def test_two_narrowings_at_once_never_add_back_what_the_other_took(run):
    company = uuid.uuid4()

    async def scenario():
        made = await new_key(company, ["credits:read", *READS])
        await asyncio.gather(
            transaction(keys.narrow, company, made.id, ["credits:read", "interviews:read"], "u1"),
            transaction(keys.narrow, company, made.id, ["credits:read", "candidates:read"], "u2"),
        )

        return await transaction(keys.get, company, made.id)

    stored = run(scenario())

    assert set(stored.permissions) < {"credits:read", *READS}


def test_keys_made_before_permissions_keep_every_api_permission_but_mcp(run):
    async def insert():
        async with Session() as session:
            await session.execute(
                text(
                    "INSERT INTO api_keys (id, company_id, name, shown, hash, created_by, created_at) "
                    "VALUES (:id, :company, 'Old', 'pz_o', :hash, 'u1', now())"
                ),
                {"id": key_id, "company": uuid.uuid4(), "hash": uuid.uuid4().hex * 2},
            )
            await session.commit()

    async def permissions():
        async with Session() as session:
            return await session.scalar(
                text("SELECT permissions FROM api_keys WHERE id = :id"), {"id": key_id}
            )

    key_id = uuid.uuid4()
    config = Config("alembic.ini")
    command.downgrade(config, "0004")

    try:
        run(insert())
    finally:
        command.upgrade(config, "head")

    assert run(permissions()) == EVERY_API_PERMISSION
