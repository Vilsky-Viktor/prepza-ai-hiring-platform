import uuid

from api.constants.api import WEBHOOK_LOG_KEPT
from api.repositories import webhook_log, webhooks


def test_a_web_hooks_log_keeps_its_latest_sends_and_goes_with_it(run):
    async def scenario():
        hook = await webhooks.add(uuid.uuid4(), "https://a.example/x", "secret", "ann", 5)
        other = await webhooks.add(uuid.uuid4(), "https://b.example/x", "secret", "ann", 5)

        for sent in range(WEBHOOK_LOG_KEPT + 3):
            await webhook_log.add(hook.id, f"e{sent}", "candidate.started", True, "delivered")

        await webhook_log.add(other.id, "x", "test", False, "500")
        kept = await webhook_log.latest(hook.id)
        others = await webhook_log.latest(other.id)
        await webhooks.remove(hook.company_id, hook.id, "u1")

        return kept, others, await webhook_log.latest(hook.id)

    kept, others, after = run(scenario())

    # The newest first, only the latest WEBHOOK_LOG_KEPT; another web hook's log untouched.
    assert len(kept) == WEBHOOK_LOG_KEPT
    assert kept[0].event_id == f"e{WEBHOOK_LOG_KEPT + 2}"
    assert [(row.ok, row.result) for row in others] == [(False, "500")]
    assert after == []
