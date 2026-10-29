"""Notifications sends a saved campaign's English texts and missing languages; each language is
queued once for the next batch."""

import uuid

from prepza_common.http.http import bearer

from generation.constants.batch_work import BatchKind
from generation.core.security import service_token

SOURCE = {"subject": "New", "text": "One.", "button": None, "missing": ["de", "fr"]}


def test_each_missing_language_of_a_campaign_is_queued_once(client, batch_store):
    campaign_id = uuid.uuid4()
    path = f"/internal/campaigns/{campaign_id}/translate"
    headers = bearer(service_token("generation"))

    answers = [client.post(path, json=SOURCE, headers=headers).status_code for _ in range(2)]

    assert answers == [202, 202]
    assert sorted(
        (row.kind, row.subject_id, row.key, row.payload["source"]["subject"])
        for row in batch_store.rows.values()
    ) == [
        (BatchKind.CAMPAIGN, campaign_id, "de", "New"),
        (BatchKind.CAMPAIGN, campaign_id, "fr", "New"),
    ]
