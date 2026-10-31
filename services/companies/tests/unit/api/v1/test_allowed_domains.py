# The company fixture is imported from the AI apps tests and named in the tests.
# ruff: noqa: F811
from testee_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.ai_apps import AI_APPS_CHANGED_BY_APP
from companies.repositories import companies
from tests.unit.api.v1.test_ai_apps import COMPANY_ID, company, sign_in, via  # noqa: F401

PATH = f"/companies/{COMPANY_ID}/allowed-domains"


def stored(monkeypatch, acme):
    async def set_allowed_domains(session, company_id, domains, allow_localhost):
        acme.allowed_domains, acme.allow_localhost = domains, allow_localhost

    monkeypatch.setattr(companies, "set_allowed_domains", set_allowed_domains)


def test_an_admin_sets_the_allowed_domains_and_the_company_shows_them(
    client, company, audited, monkeypatch
):
    stored(monkeypatch, company)
    body = {"domains": ["https://Jobs.Acme.com/careers", "*.acme.com"], "allow_localhost": True}

    saved = client.put(PATH, json=body)
    shown = client.get(f"/companies/{COMPANY_ID}").json()

    assert saved.json() == {"domains": ["jobs.acme.com", "*.acme.com"], "allow_localhost": True}
    assert shown["allowed_domains"] == ["jobs.acme.com", "*.acme.com"]
    assert shown["allow_localhost"] is True
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.EMBED_DOMAINS_CHANGED, COMPANY_ID, TargetKind.COMPANY)
    ]


def test_a_bad_domain_is_refused_and_nothing_changes(client, company, monkeypatch):
    stored(monkeypatch, company)

    for domains in (["acme.com", "co.uk"], ["*.github.io"], [f"s{n}.acme.com" for n in range(21)]):
        assert client.put(PATH, json={"domains": domains}).status_code == 422

    assert client.get(f"/companies/{COMPANY_ID}").json()["allowed_domains"] == []


def test_only_owners_and_admins_set_them_and_never_from_an_ai_app(client, company, monkeypatch):
    stored(monkeypatch, company)
    body = {"domains": ["acme.com"]}

    from_app = client.put(PATH, json=body, headers=via("mcp"))
    sign_in("vic")
    from_viewer = client.put(PATH, json=body)

    assert from_app.status_code == 403
    assert from_app.json()["detail"] == AI_APPS_CHANGED_BY_APP
    assert from_viewer.status_code == 403
    assert not company.allowed_domains
