"""Notifications sends a saved campaign's English texts and missing languages, and site a news
post's; each language is queued once for the next batch."""

import uuid

from testee_common.http.http import bearer

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


def test_each_missing_language_of_a_news_post_is_queued_once(client, batch_store):
    news_id = uuid.uuid4()
    path = f"/internal/news/{news_id}/translate"
    headers = bearer(service_token("generation"))
    source = {"title": "Practice", "text": "One.", "missing": ["de", "fr"]}

    answers = [client.post(path, json=source, headers=headers).status_code for _ in range(2)]

    assert answers == [202, 202]
    assert sorted(
        (row.kind, row.subject_id, row.key, row.payload["source"]["title"])
        for row in batch_store.rows.values()
    ) == [
        (BatchKind.NEWS, news_id, "de", "Practice"),
        (BatchKind.NEWS, news_id, "fr", "Practice"),
    ]
