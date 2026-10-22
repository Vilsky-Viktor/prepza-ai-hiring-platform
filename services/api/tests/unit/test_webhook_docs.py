import json
from datetime import UTC, datetime

import pytest

from app.helpers.webhooks import body_of
from app.main import app


@pytest.mark.parametrize(
    "event",
    [
        "candidate.finished",
        "candidate.started",
        "candidate.undelivered",
        "candidate.expired",
        "candidate.removed",
        "interview.ready",
        "test",
    ],
)
def test_the_reference_shows_each_events_body_as_its_sent(event):
    spec = app.openapi()
    body = spec["webhooks"][event]["post"]["requestBody"]["content"]["application/json"]
    name = body["schema"]["$ref"].rsplit("/", 1)[-1]
    sent = json.loads(body_of("evt_1", event, {}, datetime.now(UTC)))

    assert set(spec["components"]["schemas"][name]["properties"]) == set(sent)
    # The reference names the event's own type, as a closed set.
    kind = spec["components"]["schemas"][name]["properties"]["type"]
    assert event in kind.get("enum", [kind.get("const")])


def test_each_public_operation_has_a_short_stable_id():
    spec = app.openapi()
    ids = {
        (path, method): operation["operationId"]
        for path, item in spec["paths"].items()
        for method, operation in item.items()
    }

    assert ids[("/interviews", "get")] == "list_interviews"
    assert ids[("/interviews/{interview_id}/candidates", "post")] == "invite_candidate"
    assert ids[("/candidates/search", "post")] == "search_candidates"
    assert len(set(ids.values())) == len(ids)
