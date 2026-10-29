"""Every route taking a company's id or one of its payments' lets its owners through and refuses
another company's owner, a viewer's change and anyone signed out; superadmin routes refuse
everyone else (access_matrix); the /internal routes taking a company with one of its payments
refuse another company's, and a call without this service's token (internal_matrix;
.claude/rules/testing.md, Security)."""

import secrets
import string
from datetime import UTC, datetime
from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id

from billing.config import settings
from billing.constants.products import OwnerType
from billing.core.security import SERVICE_NAME
from billing.integrations import paddle
from billing.main import app
from billing.repositories import purchases
from tests.integration.transactions import transaction

OWNED = {"company_id", "transaction_id", "user_id"}

NOT_OWNED = {}

# A company with one of its payments: companies' support tab asks for an invoice.
INTERNAL_OWNED = {"company_id", "transaction_id"}
NOT_SCOPED = {
    "DELETE /internal/companies/{company_id}/auto-top-up": "`buyer_id` only narrows: off only "
    "when that person's card pays.",
}
KEY = (settings.service_secret, SERVICE_NAME)

VALUES = {"name": "MAX_API_KEYS"}

BODIES = {
    "PUT /companies/{company_id}/billing/currency": {"currency": "USD"},
    "PUT /superadmin/limits/{name}": {"value": 10},
}

EXCEPTIONS = {
    # Prices are for whoever pays: owners and admins.
    "GET /companies/{company_id}/billing/catalog": {"viewer": access_matrix.REFUSED},
    # Owners and admins see the invoices and failed payments of the top-ups they pay.
    "GET /companies/{company_id}/billing/invoice": {"viewer": access_matrix.REFUSED},
    "GET /companies/{company_id}/billing/payment-failure": {"viewer": access_matrix.REFUSED},
}


def transaction_id() -> str:
    """A Paddle transaction's id, in its shape."""
    alphabet = string.ascii_lowercase + string.digits

    return "txn_" + "".join(secrets.choice(alphabet) for _ in range(26))


async def side(kind: str) -> Side:
    """A company's owner and viewer, with a top-up the owner paid."""
    owner, company, paid = user_id(kind), str(uuid4()), transaction_id()
    await transaction(
        purchases.grant,
        OwnerType.COMPANY,
        company,
        10,
        1,
        paid,
        "matrix",
        owner,
        "1000",
        "USD",
        datetime.now(UTC),
    )
    ids = {"company_id": company, "transaction_id": paid, "user_id": owner}

    return Side(owner, ids, user_id(f"{kind}-viewer"))


@pytest.fixture
def world(run, monkeypatch):
    """Paddle knows each side's top-up as its owner's checkout into its company, its payment
    declined."""
    made = run(make())
    known = {
        side.ids["transaction_id"]: {
            "custom_data": {
                "owner_type": OwnerType.COMPANY,
                "owner_id": side.ids["company_id"],
                "buyer_id": side.user,
            },
            "payments": [{"error_code": "declined"}],
        }
        for side in (made.mine, made.theirs)
    }

    async def found(transaction_id, timeout):
        return known.get(transaction_id, {})

    monkeypatch.setattr(paddle, "transaction", found)

    return access_matrix.enter(monkeypatch, made)


async def make() -> World:
    return World(await side("mine"), await side("theirs"))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)


def test_every_internal_route_taking_two_ids_is_scoped_or_listed_with_why():
    assert internal_matrix.unlisted(app, INTERNAL_OWNED, NOT_SCOPED, {}) == []


@pytest.mark.parametrize(
    "route", internal_matrix.routes(app, INTERNAL_OWNED, NOT_SCOPED, {}), ids=str
)
def test_only_the_scoped_object_gets_through(route, world, run):
    found, statuses = run(internal_matrix.outcomes(app, route, world, KEY, BODIES, VALUES))

    assert found == internal_matrix.expected(route, {}), str(statuses)
