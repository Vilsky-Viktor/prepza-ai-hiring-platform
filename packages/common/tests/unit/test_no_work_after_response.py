"""No work after the response (.claude/rules/python-services.md, FastAPI on Cloud Run): request
billing throttles the CPU once a response is sent, so a background task stalls or is lost.
Every task started in the services' code is one awaited before its request ends, or listed here
with why it isn't."""

import re
from pathlib import Path

from service_code import service_code

ROOT = Path(__file__).resolve().parents[4]
STARTS = re.compile(r"\b(create_task|ensure_future|BackgroundTasks|add_task)\(|BackgroundTasks\b")

# Files allowed to start one, with why.
ALLOWED = {
    # A turn runs as a task its stream awaits in `finally`, so it ends with the request.
    "services/assistant/src/assistant/services/turns.py",
    # The instance's one Redis subscription for the bell's open streams, dropped with the last.
    "services/notifications/src/notifications/integrations/subscription.py",
    # Locally only: there's no Cloud Tasks queue, so a job calls the worker in the background.
    "services/generation/src/generation/integrations/tasks.py",
    # A spoken answer's realtime transcription reads OpenAI's events in a task, cancelled as its
    # session closes, inside the answer's WebSocket.
    "services/rounds/src/rounds/integrations/live_hearing.py",
    # The event loop's heartbeat, one per instance for its whole life, started in its lifespan:
    # no request's work. Throttled between requests, the loop then waits idle, never counted.
    "packages/common/src/prepza_common/observability/loop_watch.py",
    # Integration tests' races only: both calls are awaited before the test ends.
    "packages/common/src/prepza_common/db/lock_waits.py",
}


def test_no_task_outlives_its_request():
    files = service_code(ROOT)
    files += list(ROOT.glob("packages/common/src/prepza_common/**/*.py"))
    found = [
        str(path.relative_to(ROOT))
        for path in files
        if STARTS.search(path.read_text()) and str(path.relative_to(ROOT)) not in ALLOWED
    ]

    assert len(files) > 300
    assert found == []
