"""A bulk send started twice at once (two clicks), proven to overlap: the first start's
transaction stays open at its commit until the second is seen waiting on the send's unique key
(prepza_common.db.lock_waits)."""

import os
import uuid

from prepza_common.db.lock_waits import hold_first_commit, race

from app.constants.bulk import BulkKind
from app.storage import bulk_sends


def test_a_send_started_twice_at_once_starts_once(run, monkeypatch):
    about = str(uuid.uuid4())

    async def scenario():
        held = hold_first_commit(monkeypatch, bulk_sends)

        return await race(
            os.environ["DATABASE_URL"],
            held,
            bulk_sends.start(BulkKind.LEGAL_TERMS, about, "sam"),
            bulk_sends.start(BulkKind.LEGAL_TERMS, about, "sam"),
        )

    first, second = run(scenario())

    assert isinstance(first, uuid.UUID)
    assert second is None
