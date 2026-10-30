"""Deleting a company never deletes its questions in the shared bank (the user's rule): every
path that deletes in library (companies' interview.deleted and company.deleted, which a deleted
company, an account's erasure and a superadmin's deletion all end in; accounts' user.deleted;
generation's delete of a cancelled set; the daily job) leaves the bank copies whole, their
link to the source only cleared, and other companies still get them."""

import uuid

from sqlalchemy import text

from library.core.db import Session
from library.repositories import preparations, reuse
from library.services import housekeeping
from library.services import sets as set_service
from tests.integration.bank_factories import bank_by_id, bank_rows, shared_interview
from tests.integration.factories import a_company, direction
from tests.integration.handlers.test_deletion_events import deleted, pushed
from tests.integration.transactions import transaction


async def offered_to(company: str, embedding) -> set:
    """The bank questions a new interview of `company` would reuse for this topic."""
    found = await transaction(reuse.find, embedding, "medium", "en", 50, uuid.UUID(company))

    return {question_id for question_id, _, _ in found}


async def survived(bank_ids: list) -> tuple[list, set]:
    """Each bank copy's (source, text) now, and which of them another company is offered."""
    now = await bank_by_id(bank_ids)

    return [now.get(bank_id) for bank_id in bank_ids], await offered_to(
        a_company(str(uuid.uuid4())), direction(1.0)
    )


async def shared(company: str):
    set_id, ids = await shared_interview(company)
    copies = await bank_rows(ids)
    texts = {
        bank_id: wording for bank_id, (_, wording) in (await bank_by_id(copies.values())).items()
    }

    return set_id, [copies[question_id] for question_id in ids], texts


def assert_kept(result, bank_ids, texts):
    now, offered = result

    assert now == [(None, texts[bank_id]) for bank_id in bank_ids]
    assert set(bank_ids) <= offered


def test_a_deleted_interviews_bank_questions_stay(run):
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id, bank_ids, texts = await shared(company)
        codes = await pushed("interview.deleted", deleted(company, set_id))

        return (
            codes,
            await transaction(preparations.get, set_id),
            bank_ids,
            texts,
            await survived(bank_ids),
        )

    codes, question_set, bank_ids, texts, result = run(scenario())

    assert codes == [204, 204]
    assert question_set is None
    assert_kept(result, bank_ids, texts)


def test_a_deleted_companys_bank_questions_stay(run, monkeypatch):
    """company.deleted ends every company deletion: by its owner, by a superadmin, and with an
    account's erasure (companies deletes the companies it owns first). A batch at a time."""
    monkeypatch.setattr(preparations, "SET_DELETE_BATCH", 1)
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        first, first_ids, first_texts = await shared(company)
        second, second_ids, second_texts = await shared(company)
        codes = await pushed("company.deleted", {"company_id": company})
        gone = [await transaction(preparations.get, set_id) for set_id in (first, second)]
        bank_ids = first_ids + second_ids

        return codes, gone, bank_ids, first_texts | second_texts, await survived(bank_ids)

    codes, gone, bank_ids, texts, result = run(scenario())

    assert codes == [204, 204]
    assert gone == [None, None]
    assert_kept(result, bank_ids, texts)


def test_a_deleted_accounts_event_keeps_the_bank_questions(run):
    """user.deleted takes only the user's votes and reports; the bank and its sources stay."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        _, bank_ids, _ = await shared(company)
        sources = {bank_id: source for bank_id, (source, _) in (await bank_by_id(bank_ids)).items()}
        codes = await pushed("user.deleted", {"user_id": company, "email": "gone@example.com"})
        now = await bank_by_id(bank_ids)

        return codes, sources, {bank_id: source for bank_id, (source, _) in now.items()}

    codes, before, after = run(scenario())

    assert codes == [204, 204]
    assert after == before


def test_a_cancelled_generations_set_goes_without_its_bank_questions(run):
    """Generation deletes a set saved for a cancelled generation (DELETE /internal/interviews)."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id, bank_ids, texts = await shared(company)
        await set_service.delete(set_id)

        return bank_ids, texts, await survived(bank_ids)

    bank_ids, texts, result = run(scenario())

    assert_kept(result, bank_ids, texts)


def test_the_daily_job_keeps_unflagged_bank_questions(run):
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        _, bank_ids, _ = await shared(company)
        before = await bank_by_id(bank_ids)
        await housekeeping.daily()

        return before, await bank_by_id(bank_ids)

    before, after = run(scenario())

    assert after == before


def test_a_question_deleted_any_other_way_leaves_its_bank_copy(run):
    """The database itself keeps the rule: a deleted source only clears the bank copy's link
    (ON DELETE SET NULL), whatever deletes it."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        _, bank_ids, texts = await shared(company)

        async with Session.begin() as session:
            await session.execute(
                text(
                    "DELETE FROM questions WHERE id IN (SELECT source_question_id FROM "
                    "bank_questions WHERE id = ANY(:ids))"
                ),
                {"ids": bank_ids},
            )

        return bank_ids, texts, await survived(bank_ids)

    bank_ids, texts, result = run(scenario())

    assert_kept(result, bank_ids, texts)
