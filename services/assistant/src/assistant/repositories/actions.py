import json
from uuid import UUID

from assistant.constants.actions_flow import (
    ACTION_KEY,
    ACTION_TTL_SECONDS,
    CONVERSATION_ACTIONS_KEY,
    USER_ACTIONS_KEY,
)
from assistant.integrations.redis import get_redis


def key(action_id: UUID) -> str:
    return ACTION_KEY.format(action_id=action_id)


async def save(action_id: UUID, pending: dict) -> None:
    """A prepared action, for ACTION_TTL_SECONDS: whose it is (user, conversation, company), the
    tool, its exact arguments and its card; indexed by its user and its conversation."""
    indexes = [
        USER_ACTIONS_KEY.format(user_id=pending["user_id"]),
        CONVERSATION_ACTIONS_KEY.format(conversation_id=pending["conversation_id"]),
    ]

    async with get_redis().pipeline(transaction=True) as pipe:
        pipe.set(key(action_id), json.dumps(pending), ex=ACTION_TTL_SECONDS)

        for index in indexes:
            pipe.sadd(index, str(action_id))
            pipe.expire(index, ACTION_TTL_SECONDS)

        await pipe.execute()


async def peek(action_id: UUID) -> dict | None:
    found = await get_redis().get(key(action_id))

    return json.loads(found) if found else None


async def attach(action_id: UUID, message_id: UUID) -> None:
    """Names the answer that prepared it, once that's saved, so its card shows under it again;
    nothing when it's gone meanwhile."""
    pending = await peek(action_id)

    if pending is not None:
        pending["message_id"] = str(message_id)
        await get_redis().set(key(action_id), json.dumps(pending), keepttl=True, xx=True)


async def of_conversation(conversation_id: UUID) -> list[dict]:
    """The conversation's actions still waiting for confirmation."""
    redis = get_redis()
    ids = await redis.smembers(CONVERSATION_ACTIONS_KEY.format(conversation_id=conversation_id))
    found = [await peek(UUID(item.decode())) for item in ids]

    return [pending for pending in found if pending is not None]


async def claim(action_id: UUID) -> dict | None:
    """Takes the action, atomically: of two confirms (or a confirm and a cancel), only one gets
    it; None when it's gone (handled, or expired)."""
    found = await get_redis().getdel(key(action_id))

    return json.loads(found) if found else None


async def put_back(action_id: UUID, pending: dict) -> None:
    """Gives a claimed action back when it couldn't run at all (the user's token had expired),
    unless it was prepared again meanwhile."""
    await get_redis().set(key(action_id), json.dumps(pending), ex=ACTION_TTL_SECONDS, nx=True)


async def delete_user(user_id: str) -> None:
    """Every pending action of the user's (deleting their account). Safe to repeat."""
    redis = get_redis()
    mine = USER_ACTIONS_KEY.format(user_id=user_id)
    ids = await redis.smembers(mine)
    await redis.delete(mine, *(ACTION_KEY.format(action_id=item.decode()) for item in ids))
