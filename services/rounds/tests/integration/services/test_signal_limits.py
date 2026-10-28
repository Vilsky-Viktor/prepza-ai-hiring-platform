import uuid

import pytest
from prepza_common.auth.user import User
from prepza_common.limits.limit_list import LIMITS_KEY

from rounds.integrations.redis import get_redis
from rounds.repositories import sessions, signals
from rounds.schemas.sessions import SignalIn
from rounds.services import signals as signal_service
from tests.integration.factories import MOST_SIGNALS, created, topic
from tests.integration.transactions import transaction


@pytest.mark.parametrize("edited", [None, 3])
def test_a_question_keeps_a_limited_number_of_signals(run, edited):
    """As many as the limit's edited value, or its default when it isn't edited (read by
    services/signals.py); another question keeps its own."""
    invite_id = uuid.uuid4()
    most = edited or MOST_SIGNALS
    candidate = User(uid="cand", email="cand@example.com", email_verified=True)

    async def scenario():
        if edited:
            await get_redis().hset(LIMITS_KEY, "MAX_SIGNALS_PER_QUESTION", edited)

        try:
            [row] = await created("cand", invite_id, [topic()], 30, company_id=uuid.uuid4())
            await transaction(sessions.mark_shown, row.id)

            for _ in range(most + 5):
                await signal_service.record(row.id, SignalIn(kind="tab_leave"), candidate)

            await transaction(signals.add_signal, row.id, None, "copy", most)
            [found] = await transaction(sessions.list_for_invite, invite_id, signals=True)
        finally:
            await get_redis().hdel(LIMITS_KEY, "MAX_SIGNALS_PER_QUESTION")

        return found

    found = run(scenario())

    on_question = [signal for signal in found.signals if signal.question_id is not None]
    assert len(on_question) == most
    # Another question (here, none on screen) still keeps its own.
    assert len(found.signals) == most + 1
