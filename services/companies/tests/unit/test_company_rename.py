import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind

from app.main import app
from app.models.companies import Company, Member
from app.storage import companies

COMPANY_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}/name"


@pytest.fixture
def renamed(monkeypatch):
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin")
    ]
    names = []

    async def fake_get(_id):
        return company

    async def fake_rename(_id, name):
        if name.lower() == "taken inc":
            return False

        names.append(name)

        return True

    monkeypatch.setattr(companies, "get", fake_get)
    monkeypatch.setattr(companies, "rename", fake_rename)

    yield names

    app.dependency_overrides.clear()


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


def test_a_member_renames_the_company(client, renamed, audited):
    sign_in("bob")

    assert client.patch(URL, json={"title": "  Acme Labs "}).status_code == 204
    assert renamed == ["Acme Labs"]
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.COMPANY_RENAMED, COMPANY_ID, TargetKind.COMPANY)
    ]


def test_a_name_another_company_has_is_refused(client, renamed, audited):
    sign_in("bob")
    response = client.patch(URL, json={"title": "Taken Inc"})

    assert response.status_code == 409
    assert response.json()["detail"] == "A company with this name already exists."
    assert audited == []


def test_others_cant_rename_it(client, renamed):
    sign_in("mallory")

    assert client.patch(URL, json={"title": "Mine"}).status_code == 404
    assert renamed == []
