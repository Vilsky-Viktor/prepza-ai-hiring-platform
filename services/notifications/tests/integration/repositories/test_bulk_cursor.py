"""A bulk send's cursor names the last account read, so it's emptied once the audience is read."""

import uuid

from notifications.constants.bulk import BulkKind
from notifications.models.bulk import BulkSend
from notifications.repositories import bulk_sends
from tests.integration.transactions import transaction


def test_a_sends_cursor_is_emptied_once_its_audience_is_read(run):
    about = str(uuid.uuid4())

    async def scenario():
        send_id = await transaction(bulk_sends.start, BulkKind.LEGAL_TERMS, about, "sam")
        await transaction(bulk_sends.save_page, send_id, "", "accounts:u-1", ["u-1"], False)
        midway = await transaction(cursor_of, send_id)
        await transaction(
            bulk_sends.save_page, send_id, "accounts:u-1", "accounts:u-2", ["u-2"], True
        )

        return midway, await transaction(cursor_of, send_id)

    assert run(scenario()) == ("accounts:u-1", None)


async def cursor_of(session, send_id):
    return (await session.get(BulkSend, send_id)).prepared_after
