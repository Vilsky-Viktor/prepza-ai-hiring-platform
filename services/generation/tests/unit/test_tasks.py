import asyncio
import base64
import json
from unittest import mock

from prepza_common.http import http

from app.config.settings import settings
from app.constants.generation import RUN_GENERATION, TASK_DEADLINE_SECONDS
from app.integrations import tasks

# The real function: the autouse `queued` fixture replaces the module's attribute in tests.
from app.integrations.tasks import enqueue as real_enqueue

PAYLOAD = {"generation_id": "g-1"}


class FakeClient:
    def __init__(self):
        self.calls = []

    async def post(self, url, json, headers=None, timeout=None):
        self.calls.append((url, json, headers))

        return mock.Mock(raise_for_status=lambda: None)


def test_in_google_cloud_a_job_becomes_a_signed_cloud_task(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prepza-prod")
    monkeypatch.setattr(tasks, "access_token", lambda: "google-token")
    monkeypatch.setattr(settings, "worker_url", "https://worker.run.app")
    monkeypatch.setattr(settings, "tasks_queue", "projects/p/locations/l/queues/generation")
    monkeypatch.setattr(settings, "invoker_service_account", "invoker@p.iam.gserviceaccount.com")

    asyncio.run(real_enqueue(RUN_GENERATION, PAYLOAD))

    [(url, body, headers)] = client.calls
    request = body["task"]["httpRequest"]
    assert (
        url == "https://cloudtasks.googleapis.com/v2/projects/p/locations/l/queues/generation/tasks"
    )
    assert headers == {"Authorization": "Bearer google-token"}
    assert request["url"] == f"https://worker.run.app{RUN_GENERATION}"
    assert json.loads(base64.b64decode(request["body"])) == PAYLOAD
    assert request["oidcToken"] == {
        "serviceAccountEmail": "invoker@p.iam.gserviceaccount.com",
        "audience": "https://worker.run.app",
    }
    assert body["task"]["dispatchDeadline"] == f"{TASK_DEADLINE_SECONDS}s"


def test_locally_the_worker_is_called_directly(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setattr(settings, "worker_url", "http://generation-worker:8000")

    async def scenario():
        await real_enqueue(RUN_GENERATION, PAYLOAD)
        await asyncio.gather(*tasks.local_jobs)

    asyncio.run(scenario())

    assert client.calls == [(f"http://generation-worker:8000{RUN_GENERATION}", PAYLOAD, None)]
