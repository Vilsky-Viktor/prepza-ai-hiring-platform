import uuid
from datetime import UTC, datetime

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.verification import VerificationStatus
from companies.helpers.verification import email_on_domain, is_free_domain, website_domain
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import companies, interviews, verification

COMPANY_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}/website"


@pytest.fixture
def company(monkeypatch):
    found = Company(
        id=COMPANY_ID,
        name="Acme",
        created_at=datetime.now(UTC),
        verification_status=VerificationStatus.NONE,
    )
    found.members = [
        Member(company_id=COMPANY_ID, user_id="ann", invited_email="a@x.com", role="owner"),
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="b@x.com", role="admin"),
    ]

    async def fake_get(session, _id):
        return found

    async def fake_set(session, _id, domain, email):
        """As storage.verification.set_website does it."""
        found.website_domain = domain
        found.verified_domain = None
        found.verification_email = email
        found.decline_reason = None

        if domain is None:
            found.verification_status = VerificationStatus.NONE
        elif email is None:
            found.verification_status = VerificationStatus.WAITING_EMAIL
        else:
            found.verification_status = VerificationStatus.PENDING

    async def no_counts(session, ids):
        return {}

    monkeypatch.setattr(companies, "get", fake_get)
    monkeypatch.setattr(verification, "set_website", fake_set)
    monkeypatch.setattr(interviews, "counts", no_counts)

    yield found

    app.dependency_overrides.clear()


def approve(company):
    """As a superadmin's approval leaves it."""
    company.verification_status = VerificationStatus.APPROVED
    company.verified_domain = company.website_domain


def sign_in(uid, email, verified=True):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email, email_verified=verified
    )


def test_a_website_is_read_as_its_domain():
    assert website_domain("https://www.Acme.com/jobs?x=1") == "acme.com"
    assert website_domain("acme.co.uk") == "acme.co.uk"
    assert website_domain("not a site") is None
    assert email_on_domain("ann@eu.acme.com", "acme.com")
    assert not email_on_domain("ann@notacme.com", "acme.com")


def state(result):
    return result["website_domain"], result["verified_domain"], result["verification_status"]


def test_a_work_email_on_the_domain_sends_it_for_review_without_the_badge(client, company, audited):
    sign_in("ann", "ann@acme.com")

    result = client.put(URL, json={"website": "https://www.acme.com"}).json()

    assert state(result) == ("acme.com", None, "pending")
    assert company.verification_email == "ann@acme.com"
    assert audited == [
        (COMPANY_ID, "ann", AuditAction.VERIFICATION_REQUESTED, COMPANY_ID, TargetKind.COMPANY)
    ]


def test_a_personal_email_waits_until_a_work_one_opens_the_company(client, company):
    sign_in("ann", "ann@gmail.com")
    first = client.put(URL, json={"website": "acme.com"}).json()

    assert state(first) == ("acme.com", None, "waiting_email")

    sign_in("bob", "bob@acme.com")
    opened = client.get(f"/companies/{COMPANY_ID}").json()

    assert opened["verified_domain"] is None
    assert opened["verification_status"] == "pending"
    assert company.verification_email == "bob@acme.com"


def test_free_mail_and_unverified_emails_never_prove_it(client, company):
    sign_in("ann", "ann@gmail.com")

    assert client.put(URL, json={"website": "gmail.com"}).status_code == 422

    sign_in("ann", "ann@acme.com", verified=False)

    assert client.put(URL, json={"website": "acme.com"}).json()["verification_status"] == (
        "waiting_email"
    )


def test_opening_a_declined_company_doesnt_send_it_again(client, company):
    company.website_domain = "acme.com"
    company.verification_status = VerificationStatus.DECLINED
    sign_in("ann", "ann@acme.com")

    assert client.get(f"/companies/{COMPANY_ID}").json()["verification_status"] == "declined"


def test_a_website_is_a_registrable_domain_never_a_public_suffix():
    assert website_domain("https://jobs.acme.com") == "acme.com"
    assert website_domain("x.github.io") == "x.github.io"
    assert website_domain("ox.ac.uk") == "ox.ac.uk"

    for suffix in ("co.uk", "com.au", "github.io", "ac.uk", "https://www.co.uk"):
        assert website_domain(suffix) is None


def test_free_mail_is_matched_by_registrable_domain_in_any_country():
    free = ("yahoo.co.uk", "mail.yahoo.co.uk", "hotmail.fr", "outlook.de", "live.com.au")
    regional = ("gmx.de", "web.de", "mail.ru", "yandex.kz", "qq.com", "163.com", "naver.com")

    assert all(is_free_domain(domain) for domain in free + regional)
    assert not is_free_domain("acme.com")
    assert not is_free_domain("acme.co.uk")


def test_an_email_must_be_on_the_registrable_domain_itself():
    assert email_on_domain("x@eng.acme.com", "acme.com")
    assert email_on_domain("x@acme.co.uk", "acme.co.uk")
    assert not email_on_domain("x@ox.ac.uk", "ac.uk")
    assert not email_on_domain("x@eng.acme.com", "eng.acme.com")
    assert not email_on_domain("x@yahoo.co.uk", "yahoo.co.uk")


def test_public_suffixes_and_regional_free_mail_are_refused_as_websites(client, company):
    sign_in("ann", "ann@ox.ac.uk")

    assert client.put(URL, json={"website": "ac.uk"}).status_code == 422
    assert client.put(URL, json={"website": "github.io"}).status_code == 422
    assert client.put(URL, json={"website": "yahoo.co.uk"}).status_code == 422
    assert company.website_domain is None


def test_resaving_the_same_website_keeps_its_review_and_badge(client, company):
    sign_in("ann", "ann@acme.com")
    client.put(URL, json={"website": "acme.com"})
    sign_in("bob", "bob@gmail.com")

    assert state(client.put(URL, json={"website": "acme.com"}).json()) == (
        "acme.com",
        None,
        "pending",
    )

    approve(company)
    same = client.put(URL, json={"website": "https://www.acme.com/"}).json()

    assert state(same) == ("acme.com", "acme.com", "approved")

    other = client.put(URL, json={"website": "acme.org"}).json()

    assert state(other) == ("acme.org", None, "waiting_email")


def test_saving_a_declined_website_again_changes_nothing(client, company):
    # A declined company goes for review again only after its name or website changes.
    sign_in("ann", "ann@acme.com")
    client.put(URL, json={"website": "acme.com"})
    company.verification_status = VerificationStatus.DECLINED
    company.decline_reason = "Not the same company"

    again = client.put(URL, json={"website": "acme.com"}).json()

    assert state(again) == ("acme.com", None, "declined")
    assert again["decline_reason"] == "Not the same company"


def test_removing_the_website_removes_the_verification(client, company):
    sign_in("ann", "ann@acme.com")
    client.put(URL, json={"website": "acme.com"})
    approve(company)

    assert state(client.put(URL, json={"website": " "}).json()) == (None, None, "none")
