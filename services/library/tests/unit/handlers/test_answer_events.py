import uuid

import pytest
from event_pushes import push

from library.constants.quality import MIN_ANSWERS
from library.repositories import answer_stats
from library.services import answer_events

QUESTION_ID = uuid.uuid4()


RECORDED = {
    "question_id": str(QUESTION_ID),
    "question_text": "Which account is debited?",
    "option": "Cash",
    "options": ["Cash"],
    "correct": True,
    "credit": 1.0,
}


@pytest.fixture(autouse=True)
def emulator(monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "pubsub:8085")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-test")


@pytest.fixture(autouse=True)
def no_reviews(monkeypatch):
    reviewed = []

    async def review(question_id):
        reviewed.append(question_id)

    monkeypatch.setattr(answer_events, "review", review)

    return reviewed


@pytest.fixture
def stored(monkeypatch):
    """The answers record_answer was given."""
    stored = []

    async def record_answer(session, event_id, question_id, question_text, options, credit):
        stored.append((event_id, question_id, question_text, options, credit))

        return {question_id: MIN_ANSWERS}

    monkeypatch.setattr(answer_stats, "record_answer", record_answer)

    return stored


def test_recorded_answer_goes_into_the_question_statistics(client, stored, no_reviews):
    response = client.post("/internal/events", json=push("answer.recorded", RECORDED))

    assert response.status_code == 204
    assert stored == [("e-1", QUESTION_ID, "Which account is debited?", ["Cash"], 1.0)]
    assert no_reviews == [QUESTION_ID]


def test_a_multi_answer_answer_counts_every_option_ticked_and_its_credit(client, stored):
    partly = RECORDED | {"options": ["Cash", "Bank"], "correct": False, "credit": 2 / 3}

    client.post("/internal/events", json=push("answer.recorded", partly))

    assert stored == [("e-1", QUESTION_ID, "Which account is debited?", ["Cash", "Bank"], 2 / 3)]


@pytest.mark.parametrize(("correct", "credit"), [(True, 1.0), (False, 0.0)])
def test_an_event_from_before_multi_answer_questions_still_counts(client, stored, correct, credit):
    old = {key: value for key, value in RECORDED.items() if key not in ("options", "credit")}

    client.post("/internal/events", json=push("answer.recorded", old | {"correct": correct}))

    assert stored == [("e-1", QUESTION_ID, "Which account is debited?", ["Cash"], credit)]


def test_an_answer_isnt_reviewed_before_the_question_has_enough_to_say(
    client, monkeypatch, no_reviews
):
    original = uuid.uuid4()

    async def record_answer(*args):
        # The copy is new to answers; its bank original has been shown often.
        return {QUESTION_ID: MIN_ANSWERS - 1, original: MIN_ANSWERS + 5}

    monkeypatch.setattr(answer_stats, "record_answer", record_answer)

    response = client.post("/internal/events", json=push("answer.recorded", RECORDED))

    assert response.status_code == 204
    assert no_reviews == [original]


def test_an_event_counted_before_isnt_reviewed_again(client, monkeypatch, no_reviews):
    async def counted_before(*args):
        return None

    monkeypatch.setattr(answer_stats, "record_answer", counted_before)

    response = client.post("/internal/events", json=push("answer.recorded", RECORDED))

    assert response.status_code == 204
    assert no_reviews == []


def test_a_scored_topic_counts_each_result_in_the_candidates_group(client, monkeypatch):
    stored = []

    async def record_results(session, event_id, group, results):
        stored.append((event_id, group, [result["question_id"] for result in results]))

        return []

    monkeypatch.setattr(answer_stats, "record_results", record_results)
    result = {"question_id": str(QUESTION_ID), "question_text": "Q?", "correct": True}
    scored = {"final_score": 90, "answers": [result | {"timed_out": False}]}

    client.post("/internal/events", json=push("session.scored", scored))

    assert stored == [("e-1", "strong", [str(QUESTION_ID)])]


def test_other_events_are_accepted_without_action(client):
    response = client.post("/internal/events", json=push("preparation.shared", {}))

    assert response.status_code == 204


def test_a_failure_answers_with_an_error_so_pubsub_retries(client, monkeypatch):
    async def database_down(*args):
        raise ConnectionError("database is down")

    monkeypatch.setattr(answer_stats, "record_answer", database_down)

    with pytest.raises(ConnectionError):
        client.post("/internal/events", json=push("answer.recorded", RECORDED))


def test_pushes_without_a_google_token_are_refused_in_google_cloud(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "testee-prod")
    monkeypatch.setenv("INVOKER_AUDIENCE", "https://library.example.run.app")

    response = client.post("/internal/events", json=push("answer.recorded", RECORDED))

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("event_type", "data"),
    [
        ("answer.recorded", {k: v for k, v in RECORDED.items() if k != "question_text"}),
        ("answer.recorded", RECORDED | {"question_id": "not-a-uuid"}),
        ("session.scored", {"answers": []}),
    ],
)
def test_a_malformed_event_is_dropped_not_retried_forever(
    client, monkeypatch, no_reviews, event_type, data
):
    stored = []

    async def record(*args):
        stored.append(args)

    monkeypatch.setattr(answer_stats, "record_answer", record)
    monkeypatch.setattr(answer_stats, "record_results", record)

    response = client.post("/internal/events", json=push(event_type, data))

    # Acknowledged, so Pub/Sub stops re-sending it; nothing stored or reviewed.
    assert response.status_code == 204
    assert stored == []
    assert no_reviews == []
