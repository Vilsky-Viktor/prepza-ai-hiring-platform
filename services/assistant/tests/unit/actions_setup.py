import asyncio
import uuid

from prepza_common.auth.user import User

from app.models.answers import Turn
from app.services import actions
from app.services.registry import tools

ANN = User(uid="ann", email="ann@example.com", email_verified=True, name="Ann Lee")
BOB = User(uid="bob", email="bob@example.com", email_verified=True)
CONVERSATION = uuid.uuid4()
COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
TURN = Turn(CONVERSATION, "ann", None, "token", "en", frozenset({COMPANY}), "Ann Lee")


def prepared(redis) -> uuid.UUID:
    result = asyncio.run(actions.prepare(tools()["create_company"], {"name": "Acme"}, TURN))

    return uuid.UUID(result.block["action_id"])
