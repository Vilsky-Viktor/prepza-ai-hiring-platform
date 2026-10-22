import asyncio
import base64
import json
import logging

from prepza_common import http
from prepza_common.google import access_token, running_locally
from prepza_common.http import bearer

from app.config.settings import settings
from app.constants.generation import (
    CLOUD_TASKS_URL,
    ENQUEUE_TIMEOUT_SECONDS,
    TASK_DEADLINE_SECONDS,
)

logger = logging.getLogger(__name__)

# Local jobs running in the background; kept so they aren't garbage-collected mid-run.
local_jobs: set[asyncio.Task] = set()


async def call_locally(url: str, payload: dict) -> None:
    try:
        response = await http.get_client().post(url, json=payload, timeout=TASK_DEADLINE_SECONDS)
        response.raise_for_status()
    except Exception:
        logger.exception("Local job %s failed", url)


async def enqueue(path: str, payload: dict) -> None:
    """Runs a worker job (`path` on the worker) once. In Google Cloud it's a Cloud Task, which
    calls the worker with a signed token; locally there is no queue, so the worker is called
    directly in the background."""
    url = f"{settings.worker_url}{path}"

    if running_locally():
        job = asyncio.create_task(call_locally(url, payload))
        local_jobs.add(job)
        job.add_done_callback(local_jobs.discard)

        return

    task = {
        "httpRequest": {
            "httpMethod": "POST",
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": base64.b64encode(json.dumps(payload).encode()).decode(),
            "oidcToken": {
                "serviceAccountEmail": settings.invoker_service_account,
                "audience": settings.worker_url,
            },
        },
        "dispatchDeadline": f"{TASK_DEADLINE_SECONDS}s",
    }
    response = await http.get_client().post(
        f"{CLOUD_TASKS_URL}/v2/{settings.tasks_queue}/tasks",
        json={"task": task},
        headers=bearer(await asyncio.to_thread(access_token)),
        timeout=ENQUEUE_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
