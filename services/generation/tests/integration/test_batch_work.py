"""Batch work's table on a real database: a piece queued twice is one, sending marks it, and a
batch read twice moves a piece on once. Each test makes its own subject ids and removes them."""

import uuid

from app.storage import batch_work


def test_a_piece_is_queued_once_sent_moved_on_once_and_removed(run):
    subject = uuid.uuid4()

    async def scenario():
        await batch_work.add("news", subject, "de", "translate", {"n": 1}, {"b": 1})
        await batch_work.add("news", subject, "de", "translate", {"n": 2}, {"b": 2})
        mine = [w for w in await batch_work.unsent(500) if w.subject_id == subject]
        [piece] = mine

        try:
            await batch_work.set_batch([piece.id], "batch-x")
            sent = await batch_work.in_batch("batch-x")
            await batch_work.next_step(piece.id, "batch-x", "translate", 1, {"n": 3}, {"b": 3})
            # The same batch read again: the piece has moved on, so nothing changes.
            await batch_work.next_step(piece.id, "batch-x", "translate", 2, {"n": 4}, {"b": 4})
            moved = [w for w in await batch_work.unsent(500) if w.id == piece.id]
        finally:
            await batch_work.remove([piece.id])

        left = [w for w in await batch_work.unsent(500) if w.subject_id == subject]

        return piece, sent, moved, left

    piece, sent, moved, left = run(scenario())

    assert piece.payload == {"n": 1}
    assert [w.id for w in sent] == [piece.id]
    [after] = moved
    assert (after.attempt, after.payload, after.batch_id) == (1, {"n": 3}, None)
    assert left == []
