from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.ai.answer_votes import mirror_vote
from prepza_common.auth.tokens import same_secret
from prepza_common.limits.rate_limit import hit_or_skip

from assistant.config import settings
from assistant.constants.help_chat import NO_SUCH_ANSWER
from assistant.core.db import Session
from assistant.helpers.help_replies import help_signing_key, vote_signature
from assistant.integrations.redis import get_redis
from assistant.repositories import help_votes
from assistant.schemas.help_chat import HelpVoteIn


async def vote(answer_id: UUID, body: HelpVoteIn, address: str) -> None:
    """Saves a vote on one of the help chat's answers, signed by the page that got it, then sends
    it on to Langfuse as a score on the answer's trace when that's set up."""
    expected = vote_signature(answer_id, body.trace_id, help_signing_key(settings.service_secret))

    if not same_secret(body.signature, expected):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_SUCH_ANSWER)

    # A signed vote can be sent again and again: counted per address once it's proved real.
    await hit_or_skip(get_redis(), f"rate:help-votes:{address}", "HELP_VOTES_PER_IP_HOUR")

    async with Session.begin() as session:
        await help_votes.save(session, answer_id, body.trace_id, body.value)

    async def current() -> int | None:
        async with Session() as session:
            return await help_votes.vote_of(session, answer_id)

    await mirror_vote(body.trace_id, current)
