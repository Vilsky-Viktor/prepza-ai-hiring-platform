import base64
import io
import uuid
from datetime import UTC, datetime

import pytest
from PIL import Image
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.brand import PREPZA_COLORS
from app.helpers.logos import logo_path, logo_type
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.storage import companies, interviews, invites

COMPANY_ID = uuid.uuid4()


def png() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(out, "PNG")

    return out.getvalue()


PNG = png()


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def company(monkeypatch):
    found = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC), logo_version=0)
    found.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin")
    ]
    saved = {}

    async def fake_get(_company_id):
        return found

    async def fake_set_logo(company_id, content, media_type):
        saved["logo"] = (content, media_type)
        found.logo_type = media_type
        found.logo_version += 1

    async def fake_get_logo(_company_id):
        return (PNG, "image/png") if found.logo_type else None

    monkeypatch.setattr(companies, "get", fake_get)
    monkeypatch.setattr(companies, "set_logo", fake_set_logo)
    monkeypatch.setattr(companies, "get_logo", fake_get_logo)

    return found, saved


def test_only_png_jpeg_and_webp_up_to_500_kb_are_logos():
    assert logo_type(PNG) == "image/png"
    assert logo_type(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert logo_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert logo_type(b"<svg onload=alert(1)>") is None
    assert logo_type(PNG + b"0" * 500_001) is None


def test_an_admin_uploads_a_logo_whose_address_changes_with_each_upload(client, company, audited):
    _, saved = company
    sign_in("bob")
    url = f"/companies/{COMPANY_ID}/logo"

    first = client.put(url, json={"image": base64.b64encode(PNG).decode()}).json()
    second = client.put(url, json={"image": base64.b64encode(PNG).decode()}).json()

    content, media_type = saved["logo"]
    assert media_type == "image/png"
    assert Image.open(io.BytesIO(content)).getpixel((0, 0)) == (10, 20, 30)
    assert first["logo_url"] == f"/api/companies/companies/{COMPANY_ID}/logo?v=1"
    assert second["logo_url"].endswith("?v=2")
    assert (
        audited
        == [(COMPANY_ID, "bob", AuditAction.LOGO_CHANGED, COMPANY_ID, TargetKind.COMPANY)] * 2
    )


def test_a_logo_that_isnt_an_image_is_refused(client, company, audited):
    _, saved = company
    sign_in("bob")
    svg = base64.b64encode(b"<svg></svg>").decode()

    assert client.put(f"/companies/{COMPANY_ID}/logo", json={"image": svg}).status_code == 422
    assert saved == {} and audited == []


def test_someone_outside_the_company_cant_change_its_logo(client, company):
    sign_in("mallory")
    image = base64.b64encode(PNG).decode()

    assert client.put(f"/companies/{COMPANY_ID}/logo", json={"image": image}).status_code == 404
    assert client.delete(f"/companies/{COMPANY_ID}/logo").status_code == 404


def test_the_logo_is_served_to_anyone_and_cached_for_good(client, company):
    found, _ = company

    assert client.get(f"/companies/{COMPANY_ID}/logo").status_code == 404

    found.logo_type = "image/png"
    response = client.get(f"/companies/{COMPANY_ID}/logo")

    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert "immutable" in response.headers["cache-control"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_the_candidate_and_members_see_the_brand_others_dont(client, company, monkeypatch):
    found, _ = company
    found.logo_type = "image/png"
    found.logo_version = 3
    invite_id = uuid.uuid4()
    interview = Interview(id=uuid.uuid4(), company_id=COMPANY_ID, pass_mark=70)
    invite = CandidateInvite(
        id=invite_id, interview_id=interview.id, email="ann@example.com", user_id="ann"
    )

    async def fake_invite(_invite_id):
        return invite

    async def fake_interview(_interview_id):
        return interview

    monkeypatch.setattr(invites, "get", fake_invite)
    monkeypatch.setattr(interviews, "get", fake_interview)
    url = f"/candidates/{invite_id}/brand"

    sign_in("ann")
    candidate = client.get(url).json()
    sign_in("bob")
    member = client.get(url)
    sign_in("mallory")
    stranger = client.get(url)

    assert candidate == {
        "company": "Acme",
        "logo_url": logo_path(found),
        "return_url": None,
        # No colors of its own: prepza's, by theme; and the candidate's own theme.
        "brand_colors": PREPZA_COLORS,
        "theme": None,
        "brand_style": {"font": "poppins_geist", "radius": 14, "button_radius": 14},
    }
    assert member.status_code == 200
    assert stranger.status_code == 404
