from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from tests.unit.api_keys import KEY
from tests.unit.conftest import COMPANY, sign_in

SECRET = "test-secret-that-is-at-least-32-bytes"
KEYS = f"/manage/keys?company_id={COMPANY}"
# What Google's load balancer appends: the client, then itself.
FROM_ALLOWED = {"X-Forwarded-For": "203.0.113.7, 34.1.2.3", **bearer(KEY)}
FROM_ELSEWHERE = {"X-Forwarded-For": "198.51.100.9, 34.1.2.3", **bearer(KEY)}
# A client can put anything first; only the entry before the load balancer's counts.
SPOOFED = {"X-Forwarded-For": "203.0.113.7, 198.51.100.9, 34.1.2.3", **bearer(KEY)}


def test_a_key_limited_to_addresses_works_only_from_them(client, companies_api, key, stored):
    key.allowed_ips = ["203.0.113.0/24"]

    allowed = client.get("/interviews", headers=FROM_ALLOWED)
    refused = client.get("/interviews", headers=FROM_ELSEWHERE)
    spoofed = client.get("/interviews", headers=SPOOFED)

    assert allowed.status_code == 200
    assert refused.status_code == 403
    assert refused.json()["code"] == "ip_not_allowed"
    assert refused.json()["detail"] == (
        "This API key can't be used from this IP address. Add the address to the key's allowed "
        "IPs in prepza, or call from an allowed one."
    )
    assert spoofed.status_code == 403
    # A refused call doesn't use up the company's requests.
    assert stored["counted"] == [f"rate:api:{COMPANY}"]


def test_a_key_without_addresses_works_from_anywhere(client, companies_api, key):
    assert client.get("/interviews", headers=FROM_ELSEWHERE).status_code == 200


def test_the_mcp_server_passes_the_agents_address_on(client, companies_api, key):
    key.allowed_ips = ["2001:db8::/32"]
    headers = {"Authorization": "Bearer " + issue_token("assistant", "api", SECRET)}

    def verify(**extra):
        return client.post("/internal/keys/verify", json={"key": KEY, **extra}, headers=headers)

    assert verify(ip="2001:db8::7").status_code == 200
    assert verify(ip="2001:db9::7").status_code == 403
    # Without the address, a key limited to some refuses.
    assert verify().status_code == 403


def test_an_owner_sets_a_keys_addresses_when_making_it_and_after(client, companies_api, stored):
    sign_in()
    made = client.post(
        KEYS,
        json={"name": "Site", "expiry": "1", "allowed_ips": ["203.0.113.7/32", "2001:db8::/32"]},
    ).json()
    path = f"/manage/keys/{made['id']}/allowed-ips?company_id={COMPANY}"
    changed = client.put(path, json={"allowed_ips": ["10.0.0.0/8"]})
    listed = client.get(f"/manage?company_id={COMPANY}").json()["keys"][0]
    cleared = client.put(path, json={"allowed_ips": []})

    assert made["allowed_ips"] == ["203.0.113.7", "2001:db8::/32"]
    assert changed.json()["allowed_ips"] == ["10.0.0.0/8"]
    assert listed["allowed_ips"] == ["10.0.0.0/8"]
    assert cleared.json()["allowed_ips"] == []


def test_a_bad_address_is_refused_and_nothing_changes(client, companies_api, stored):
    sign_in()
    made = client.post(KEYS, json={"name": "Site", "expiry": "1"}).json()
    path = f"/manage/keys/{made['id']}/allowed-ips?company_id={COMPANY}"

    bad = client.put(path, json={"allowed_ips": ["203.0.113.7", "acme.com"]})
    too_many = client.put(path, json={"allowed_ips": [f"10.0.0.{n}" for n in range(51)]})
    on_create = client.post(KEYS, json={"name": "B", "expiry": "1", "allowed_ips": ["10.0.0.5/24"]})

    assert bad.status_code == 422
    assert too_many.status_code == 422
    assert on_create.status_code == 422
    assert stored["keys"][0].allowed_ips == []
    assert len(stored["keys"]) == 1


def test_only_owners_and_admins_set_a_keys_addresses(client, companies_api, key):
    path = f"/manage/keys/{key.id}/allowed-ips?company_id={COMPANY}"
    companies_api["roles"] = {"u1": "viewer"}
    sign_in()

    assert client.put(path, json={"allowed_ips": ["203.0.113.7"]}).status_code == 403
    assert key.allowed_ips == []

    companies_api["roles"] = {"u1": "owner"}

    assert (
        client.put(
            path.replace(str(key.id), "00000000-0000-0000-0000-000000000000"),
            json={"allowed_ips": []},
        ).status_code
        == 404
    )
