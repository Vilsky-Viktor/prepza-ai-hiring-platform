"""Why a checkout's payment failed: decided here from Paddle's latest attempt, only for the buyer's
own checkout into that company."""

import asyncio
import uuid

import httpx
import pytest

from billing.constants.payment_failures import PaymentFailure
from billing.helpers.payment_failures import latest_failure
from billing.integrations import paddle
from billing.services import payment_failures

TXN = "txn_01aaaaaaaaaaaaaaaaaaaaaaaa"
COMPANY_ID = str(uuid.uuid4())
PATH = f"/companies/{COMPANY_ID}/billing/payment-failure"
OURS = {"owner_type": "company", "owner_id": COMPANY_ID, "buyer_id": "bob"}


def attempt(code, method="card"):
    return {"error_code": code, "status": "error", "method_details": {"type": method}}


def transaction(*attempts, custom=OURS):
    """Paddle lists the newest attempt first."""
    return {"custom_data": custom, "payments": list(attempts)}


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("declined", PaymentFailure.CARD_DECLINED),
        ("declined_not_retryable", PaymentFailure.CARD_DECLINED),
        ("blocked_card", PaymentFailure.CARD_DECLINED),
        ("fraud", PaymentFailure.CARD_DECLINED),
        ("not_enough_balance", PaymentFailure.INSUFFICIENT_FUNDS),
        ("expired_card", PaymentFailure.EXPIRED_CARD),
        ("invalid_payment_details", PaymentFailure.INVALID_DETAILS),
        ("authentication_failed", PaymentFailure.AUTHENTICATION_FAILED),
        ("prepaid_card_not_supported", PaymentFailure.CARD_NOT_SUPPORTED),
        ("transaction_not_permitted", PaymentFailure.CARD_NOT_SUPPORTED),
        ("issuer_unavailable", PaymentFailure.TRY_LATER),
        ("system_error", PaymentFailure.TRY_LATER),
        ("unknown", PaymentFailure.OTHER),
        ("a_code_paddle_adds_later", PaymentFailure.OTHER),
    ],
)
def test_a_cards_failure_is_named_by_what_the_buyer_can_do(code, reason):
    assert latest_failure(transaction(attempt(code))) == reason


def test_a_wallets_vague_failure_is_the_methods_and_a_clear_one_keeps_its_reason():
    assert latest_failure(transaction(attempt("declined", "google-pay"))) == (
        PaymentFailure.PAYMENT_METHOD_FAILED
    )
    assert latest_failure(transaction(attempt(None, "paypal"))) == (
        PaymentFailure.PAYMENT_METHOD_FAILED
    )
    assert latest_failure(transaction(attempt("expired_card", "apple-pay"))) == (
        PaymentFailure.EXPIRED_CARD
    )


def test_only_the_latest_attempt_counts_and_one_without_a_code_yet_says_nothing():
    newest_first = transaction(attempt("expired_card"), attempt("not_enough_balance"))

    assert latest_failure(newest_first) == PaymentFailure.EXPIRED_CARD
    assert latest_failure(transaction(attempt(None))) is None
    assert latest_failure(transaction()) is None


def answering(found):
    async def read(transaction_id, timeout):
        if isinstance(found, Exception):
            raise found

        return found

    return read


def not_found():
    request = httpx.Request("GET", "https://sandbox-api.paddle.com/transactions/x")

    return httpx.HTTPStatusError("404", request=request, response=httpx.Response(404))


@pytest.mark.parametrize(
    ("found", "status", "body"),
    [
        (transaction(attempt("not_enough_balance")), 200, {"reason": "insufficient_funds"}),
        # Another buyer's checkout into the same company, or another company's.
        (transaction(attempt("declined"), custom={**OURS, "buyer_id": "eve"}), 404, None),
        (transaction(attempt("declined"), custom={**OURS, "owner_id": "other"}), 404, None),
        (not_found(), 404, None),
        # Paddle down or slow: the buyer still gets the general advice.
        (httpx.ConnectError("no route"), 200, {"reason": "other"}),
    ],
)
def test_the_route_answers_only_for_the_buyers_own_checkout(
    client, editor, monkeypatch, found, status, body
):
    monkeypatch.setattr(paddle, "transaction", answering(found))
    editor("bob")

    response = client.get(PATH, params={"transaction_id": TXN})

    assert response.status_code == status

    if body is not None:
        assert response.json() == body


def test_an_id_that_isnt_a_transactions_never_reaches_paddle(client, editor, monkeypatch):
    read = []
    monkeypatch.setattr(paddle, "transaction", lambda *args: read.append(args))
    editor("bob")

    response = client.get(PATH, params={"transaction_id": "../subscriptions"})

    assert response.status_code == 422
    assert read == []


def test_the_route_needs_a_signed_in_user(client):
    response = client.get(PATH, params={"transaction_id": TXN})

    assert response.status_code == 401


def test_an_attempt_whose_code_comes_late_is_read_again(monkeypatch, caplog):
    reads = iter([transaction(attempt(None)), transaction(attempt("expired_card"))])

    async def read(transaction_id, timeout):
        return next(reads)

    async def no_wait(seconds):
        return None

    monkeypatch.setattr(paddle, "transaction", read)
    monkeypatch.setattr(payment_failures.asyncio, "sleep", no_wait)

    caplog.set_level("INFO")

    found = asyncio.run(payment_failures.failure("company", COMPANY_ID, "bob", TXN))

    assert found == PaymentFailure.EXPIRED_CARD
    # The log says how it was decided, with the transaction's id only.
    assert f"{TXN}: expired_card after 2 reads (error code expired_card)" in caplog.text


@pytest.mark.parametrize(
    ("found", "why"),
    [
        (transaction(attempt(None)), "after 4 reads (no error code yet)"),
        (httpx.ReadTimeout("slow"), "after 1 reads (Paddle unreachable: ReadTimeout)"),
    ],
)
def test_a_failure_without_a_reason_logs_why(monkeypatch, caplog, found, why):
    async def no_wait(seconds):
        return None

    monkeypatch.setattr(paddle, "transaction", answering(found))
    monkeypatch.setattr(payment_failures.asyncio, "sleep", no_wait)
    caplog.set_level("INFO")

    found = asyncio.run(payment_failures.failure("company", COMPANY_ID, "bob", TXN))

    assert found == PaymentFailure.OTHER
    assert f"{TXN}: other {why}" in caplog.text
