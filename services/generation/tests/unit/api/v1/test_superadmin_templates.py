import uuid

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from generation.main import app
from generation.models.generation import Generation
from generation.repositories import generations


@pytest.fixture
def created(monkeypatch):
    """Generations recorded, not run; Ann is the only superadmin."""
    rows = []

    async def create(
        owner_uid, text, company_id=None, language="en", generation_id=None, kind="interview"
    ):
        row = Generation(
            id=uuid.uuid4(),
            owner_uid=owner_uid,
            text=text,
            kind=kind,
            status="queued",
            language=language,
        )
        rows.append(row)

        return row

    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    monkeypatch.setattr(generations, "create", create)

    yield rows

    app.dependency_overrides.clear()


def sign_in(email):
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1",
        email=email,
        email_verified=True,
        sign_in_provider="google.com",
    )


def test_a_superadmin_starts_a_template(client, created):
    sign_in("ann@example.com")

    response = client.post("/superadmin/templates", json={"text": "Senior accountant"})

    assert response.status_code == 201
    assert [(row.kind, row.company_id) for row in created] == [("template", None)]


def test_anyone_else_cant(client, created):
    sign_in("eve@example.com")

    assert (
        client.post("/superadmin/templates", json={"text": "Senior accountant"}).status_code == 404
    )
    assert created == []


def test_a_company_generation_isnt_reachable_through_admin_routes(client, created, monkeypatch):
    sign_in("ann@example.com")

    async def get(_generation_id):
        return Generation(id=uuid.uuid4(), kind="interview", status="running")

    monkeypatch.setattr(generations, "get", get)

    assert client.get(f"/superadmin/generations/{uuid.uuid4()}").status_code == 404
