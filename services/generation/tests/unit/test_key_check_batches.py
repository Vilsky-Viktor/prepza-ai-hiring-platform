import asyncio
import uuid

from app.constants.quality import MAX_DIRECT_KEY_CHECKS, QualityFlag
from app.integrations import library, openai_batch
from app.models.key_checks import KeyCheck as KeyCheckRow
from app.services import key_check_batches
from app.storage import key_checks
from tests.unit.test_verify import TEXT, context, question
from tests.unit.test_verify_multi import TEXT as MULTI_TEXT
from tests.unit.test_verify_multi import multi_answer as multi_answer_question

KEPT = uuid.uuid4()
GONE = uuid.uuid4()


class FakeStore:
    """key_checks storage in memory: question id -> batch id (None while waiting)."""

    def __init__(self, rows):
        self.rows = dict(rows)

    def install(self, monkeypatch):
        async def unsent(limit):
            return [row(qid) for qid, batch in self.rows.items() if batch is None]

        async def sent_batches():
            return sorted({batch for batch in self.rows.values() if batch})

        async def in_batch(batch_id):
            return [row(qid) for qid, batch in self.rows.items() if batch == batch_id]

        async def set_batch(question_ids, batch_id):
            self.rows.update({qid: batch_id for qid in question_ids})

        async def remove(question_ids):
            for qid in question_ids:
                self.rows.pop(qid, None)

        for name, fake in [
            ("unsent", unsent),
            ("sent_batches", sent_batches),
            ("in_batch", in_batch),
            ("set_batch", set_batch),
            ("remove", remove),
        ]:
            monkeypatch.setattr(key_checks, name, fake)


def row(question_id, marked_answer="Credit cash"):
    return KeyCheckRow(question_id=question_id, question_text=TEXT, marked_answer=marked_answer)


def flagged(flag=QualityFlag.WRONG_KEY):
    """The question as the library has it now: flagged for its key unless a test says not."""
    return question().model_copy(update={"flag": flag})


def library_with(monkeypatch, existing, flag=QualityFlag.WRONG_KEY):
    async def fake_context(question_id):
        return context() if question_id in existing else None

    async def fake_quality(question_id):
        return flagged(flag) if question_id in existing else None

    monkeypatch.setattr(library, "get_question_context", fake_context)
    monkeypatch.setattr(library, "get_question_quality", fake_quality)


def test_waiting_checks_go_out_in_one_batch(monkeypatch):
    store = FakeStore({KEPT: None, GONE: None})
    store.install(monkeypatch)
    library_with(monkeypatch, {KEPT})
    sent = {}

    async def fake_submit(requests):
        sent.update(requests)

        return "batch-1"

    monkeypatch.setattr(openai_batch, "submit", fake_submit)

    asyncio.run(key_check_batches.submit_pending())

    assert list(sent) == [str(KEPT)]
    assert sent[str(KEPT)]["reasoning_effort"] == "medium"
    system, question = sent[str(KEPT)]["messages"]
    # The checker's role first, the question after; the schema is enforced, as for checks made
    # at once.
    assert system["role"] == "system" and question["role"] == "user"
    assert TEXT in question["content"] and TEXT not in system["content"]
    assert sent[str(KEPT)]["response_format"]["json_schema"]["strict"] is True
    # A question deleted since it was flagged is dropped.
    assert store.rows == {KEPT: "batch-1"}


def test_a_finished_batch_is_applied_and_bad_replies_are_checked_right_away(monkeypatch):
    other = uuid.uuid4()
    store = FakeStore({KEPT: "batch-1", other: "batch-1"})
    store.install(monkeypatch)
    library_with(monkeypatch, {KEPT, other})
    applied = []

    async def fake_status(batch_id):
        return "completed", "file-1"

    async def fake_results(file_id):
        return {str(KEPT): '{"correct_indexes": [0]}', str(other): None}, []

    async def fake_apply(question_id, question, context, result):
        applied.append((question_id, result.correct_indexes))

    async def fake_check_now(question_id, question, context):
        applied.append((question_id, "checked now"))

    monkeypatch.setattr(openai_batch, "status", fake_status)
    monkeypatch.setattr(openai_batch, "results", fake_results)
    monkeypatch.setattr(key_check_batches, "apply_key_check", fake_apply)
    monkeypatch.setattr(key_check_batches, "check_key", fake_check_now)

    asyncio.run(key_check_batches.collect_finished())

    assert sorted(applied, key=str) == sorted([(KEPT, [0]), (other, "checked now")], key=str)
    assert store.rows == {}


def test_an_expired_batch_is_sent_again(monkeypatch):
    store = FakeStore({KEPT: "batch-1"})
    store.install(monkeypatch)

    async def fake_status(batch_id):
        return "expired", None

    monkeypatch.setattr(openai_batch, "status", fake_status)

    asyncio.run(key_check_batches.collect_finished())

    assert store.rows == {KEPT: None}


def test_an_expired_batchs_results_apply_and_only_the_rest_go_out_again(monkeypatch):
    other = uuid.uuid4()
    store = FakeStore({KEPT: "batch-1", other: "batch-1"})
    store.install(monkeypatch)
    library_with(monkeypatch, {KEPT, other})
    applied = []

    async def fake_status(batch_id):
        return "expired", "file-1"

    async def fake_results(file_id):
        return {str(KEPT): '{"correct_indexes": [0]}'}, []

    async def fake_apply(question_id, question, context, result):
        applied.append(question_id)

    async def never(question_id, question, context):
        raise AssertionError("checked at full price")

    monkeypatch.setattr(openai_batch, "status", fake_status)
    monkeypatch.setattr(openai_batch, "results", fake_results)
    monkeypatch.setattr(key_check_batches, "apply_key_check", fake_apply)
    monkeypatch.setattr(key_check_batches, "check_key", never)

    asyncio.run(key_check_batches.collect_finished())

    assert applied == [KEPT]
    assert store.rows == {other: None}


def test_an_empty_finished_batch_checks_only_a_few_right_away(monkeypatch):
    ids = [uuid.uuid4() for _ in range(MAX_DIRECT_KEY_CHECKS + 5)]
    store = FakeStore(dict.fromkeys(ids, "batch-1"))
    store.install(monkeypatch)
    library_with(monkeypatch, set(ids))
    checked = []

    async def fake_status(batch_id):
        return "completed", None

    async def fake_check_now(question_id, question, context):
        checked.append(question_id)

    monkeypatch.setattr(openai_batch, "status", fake_status)
    monkeypatch.setattr(key_check_batches, "check_key", fake_check_now)

    asyncio.run(key_check_batches.collect_finished())

    assert len(checked) == MAX_DIRECT_KEY_CHECKS
    # The rest go out in the next batch.
    assert store.rows == dict.fromkeys(set(ids) - set(checked), None)


def test_a_running_batch_is_left_alone(monkeypatch):
    store = FakeStore({KEPT: "batch-1"})
    store.install(monkeypatch)

    async def fake_status(batch_id):
        return "in_progress", None

    monkeypatch.setattr(openai_batch, "status", fake_status)

    asyncio.run(key_check_batches.collect_finished())

    assert store.rows == {KEPT: "batch-1"}


def test_a_result_for_a_question_fixed_or_rekeyed_since_is_dropped(monkeypatch):
    applied = []

    async def fake_apply(question_id, question, context, result):
        applied.append(question_id)

    monkeypatch.setattr(key_check_batches, "apply_key_check", fake_apply)
    reply = '{"correct_indexes": [1]}'

    # Kept or fixed since (or this result was applied already): no longer flagged for its key.
    library_with(monkeypatch, {KEPT}, flag=None)
    asyncio.run(key_check_batches.apply_reply(row(KEPT), reply))
    # Its key moved since the check was queued.
    library_with(monkeypatch, {KEPT})
    asyncio.run(key_check_batches.apply_reply(row(KEPT, "Debit cash"), reply))
    # Still as it was: the result applies; a check queued before keys were kept too.
    asyncio.run(key_check_batches.apply_reply(row(KEPT), reply))
    asyncio.run(key_check_batches.apply_reply(row(KEPT, None), reply))

    assert applied == [KEPT, KEPT]


def test_a_batched_result_for_a_multi_answer_question_applies_to_its_marked_set(monkeypatch):
    applied = []

    async def fake_apply(question_id, question, context, result):
        applied.append((question_id, result.correct_indexes))

    async def multi_answer(question_id):
        return multi_answer_question().model_copy(update={"flag": QualityFlag.WRONG_KEY})

    library_with(monkeypatch, {KEPT})
    monkeypatch.setattr(library, "get_question_quality", multi_answer)
    monkeypatch.setattr(key_check_batches, "apply_key_check", fake_apply)
    reply = '{"correct_indexes": [0, 2]}'

    def queued(marked):
        return KeyCheckRow(question_id=KEPT, question_text=MULTI_TEXT, marked_answer=marked)

    # Queued against one of its marked options only, or another set: its key moved since.
    asyncio.run(key_check_batches.apply_reply(queued("Debit cash"), reply))
    asyncio.run(key_check_batches.apply_reply(queued("Debit cash\nCredit revenue"), reply))
    asyncio.run(key_check_batches.apply_reply(queued("Debit cash\nCredit cash"), reply))

    assert applied == [(KEPT, [0, 2])]
