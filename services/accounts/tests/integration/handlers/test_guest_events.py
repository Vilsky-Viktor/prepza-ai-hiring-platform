"""A deleted guest invite's guest goes from accounts: its accepted terms and its sign-in."""

import uuid

import httpx
from event_pushes import push

from accounts.main import app
from accounts.repositories import legal
from accounts.services import guest_events
from tests.integration.transactions import transaction


def test_a_deleted_guests_rows_and_sign_in_go_and_others_stay_however_often_it_comes(
    run, monkeypatch
):
    guest, other = f"guest-{uuid.uuid4()}", f"user-{uuid.uuid4()}"
    signed_out = []
    monkeypatch.setattr(guest_events, "delete_sign_in", signed_out.append)

    async def scenario():
        for user_id in (guest, other):
            await transaction(legal.accept_terms, user_id, "2026-10-10")

        # A user who isn't a guest is never taken from this event.
        event = push("guests.deleted", {"user_ids": [guest, other]}, str(uuid.uuid4()))
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://accounts") as client:
            codes = [(await client.post("/internal/events", json=event)).status_code for _ in "ab"]

        return (
            codes,
            await transaction(legal.accepted_terms, guest),
            len(await transaction(legal.accepted_terms, other)),
        )

    codes, terms, other_terms = run(scenario())

    assert codes == [204, 204]
    assert (terms, other_terms) == ([], 1)
    assert signed_out == [guest, guest]
