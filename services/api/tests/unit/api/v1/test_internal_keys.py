from datetime import UTC, datetime, timedelta

from prepza_common.auth.service_auth import issue_token

from api.constants.permissions import Permission
from tests.unit.api_keys import KEY
from tests.unit.conftest import COMPANY

SECRET = "test-secret-that-is-at-least-32-bytes"
HEADERS = {"Authorization": "Bearer " + issue_token("assistant", "api", SECRET)}


def verify(client, raw=KEY, headers=HEADERS):
    return client.post("/internal/keys/verify", json={"key": raw}, headers=headers)


def test_a_working_key_answers_its_company_maker_and_permissions(
    client, companies_api, key, stored
):
    key.permissions = [Permission.INTERVIEWS_READ, Permission.MCP]

    response = verify(client)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(key.id),
        "company_id": str(COMPANY),
        "created_by": "u1",
        "permissions": ["interviews:read", "mcp"],
    }
    assert stored["used"] == [key.id]


def test_an_unknown_or_expired_key_is_refused(client, companies_api, key):
    unknown = verify(client, "pz_unknown")
    key.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    expired = verify(client)

    assert unknown.status_code == 401
    assert expired.status_code == 401
    assert expired.json()["detail"] == "This API key has expired"


def test_a_key_whose_maker_cant_edit_is_refused(client, companies_api, key):
    companies_api["roles"]["u1"] = "viewer"

    assert verify(client).status_code == 401


def test_a_verification_counts_against_the_companys_limit(client, companies_api, key, stored):
    stored["limited"] = True

    assert verify(client).status_code == 429
