"""A deleted guest invite's guest goes from library: its ratings and reports of questions."""

import uuid

import httpx
from event_pushes import push

from library.main import app
from library.repositories import feedback
from tests.integration.factories import interview, question_ids
from tests.integration.transactions import transaction


def test_a_deleted_guests_rows_go_and_others_stay_however_often_it_comes(run):
    guest, other = f"guest-{uuid.uuid4()}", f"user-{uuid.uuid4()}"

    async def scenario():
        set_id = await interview("Guests")
        first, second, _ = await question_ids(set_id)

        for user_id in (guest, other):
            await transaction(feedback.rate_question, first, user_id, 1)

        await transaction(feedback.report_question, second, guest, "unclear", "Two answers fit.")
        # A user who isn't a guest is never taken from this event.
        event = push("guests.deleted", {"user_ids": [guest, other]}, str(uuid.uuid4()))
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://library") as client:
            codes = [(await client.post("/internal/events", json=event)).status_code for _ in "ab"]

        return (
            codes,
            await transaction(feedback.my_question_rating, first, guest),
            await transaction(feedback.has_reported, second, guest),
            await transaction(feedback.my_question_rating, first, other),
        )

    codes, rating, reported, other_rating = run(scenario())

    assert codes == [204, 204]
    assert (rating, reported) == (None, False)
    assert other_rating == 1
