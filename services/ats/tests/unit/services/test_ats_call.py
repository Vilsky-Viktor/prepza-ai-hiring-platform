import asyncio
import uuid

from ats.integrations import greenhouse, workable
from ats.models.ats import AtsConnection
from ats.services import ats as integrations


def test_a_client_gets_only_its_own_credentials_not_the_web_hooks_secret(monkeypatch):
    connection = AtsConnection(id=uuid.uuid4(), provider="greenhouse", status="connected")
    asked = []

    async def credentials(found):
        return {"client_id": "id", "client_secret": "secret", "webhook_secret": "hook"}

    async def listed(client_id, client_secret, path, params):
        asked.append((client_id, client_secret, path))

        return [{"id": 7, "name": "Accountant"}]

    monkeypatch.setattr(integrations, "credentials", credentials)
    monkeypatch.setattr(greenhouse, "_list", listed)

    assert asyncio.run(integrations.jobs(connection)) == [{"id": "7", "name": "Accountant"}]
    assert asked == [("id", "secret", "/jobs")]


def test_only_a_workable_connection_cancels_workable_subscriptions(monkeypatch):
    connection = AtsConnection(id=uuid.uuid4(), provider="greenhouse", status="connected")
    cancelled = []

    async def credentials(found):
        return {"client_id": "id", "client_secret": "secret", "webhook_secret": "hook"}

    async def unsubscribe(subdomain, token, subscription_id):
        cancelled.append(subscription_id)

    monkeypatch.setattr(integrations, "credentials", credentials)
    monkeypatch.setattr(workable, "unsubscribe", unsubscribe)

    # Disconnecting Greenhouse while Workable has linked jobs: theirs are left alone.
    asyncio.run(integrations.unsubscribe(connection, ["sub-1"]))

    assert cancelled == []
