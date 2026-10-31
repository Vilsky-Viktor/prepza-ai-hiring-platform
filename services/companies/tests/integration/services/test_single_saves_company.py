"""An owner or admin's change to the company is one save with its line in the action log: when
the log's line fails, the change isn't kept, so the retry finds it still to do."""

import uuid

import pytest
from testee_common.auth.user import User

from companies.constants.brand import BrandFont
from companies.repositories import audit, companies
from companies.services import company_settings, verification
from tests.integration import factories
from tests.integration.broken import DatabaseWentAway, broken
from tests.integration.transactions import transaction


async def owned() -> tuple:
    """A company and its owner, signed in."""
    owner = f"owner-{uuid.uuid4()}"
    company = await factories.company(f"Saves {uuid.uuid4()}", owner, f"{owner}@acme.com")

    return company, User(uid=owner, email=f"{owner}@acme.com", email_verified=True)


def test_a_rename_whose_log_line_fails_keeps_the_old_name(run, monkeypatch):
    monkeypatch.setattr(audit, "record", broken)

    async def scenario():
        company, user = await owned()

        with pytest.raises(DatabaseWentAway):
            await company_settings.rename(company, user.uid, f"Renamed {uuid.uuid4()}")

        return company.name, (await transaction(companies.get, company.id)).name

    before, after = run(scenario())

    assert after == before


def test_stopping_ai_apps_whose_log_line_fails_keeps_them_allowed(run, monkeypatch):
    monkeypatch.setattr(audit, "record", broken)

    async def scenario():
        company, user = await owned()

        with pytest.raises(DatabaseWentAway):
            await company_settings.set_ai_apps(company.id, user, False, None)

        return (await transaction(companies.get, company.id)).ai_apps_off_at

    assert run(scenario()) is None


@pytest.mark.parametrize(
    ("change", "args"),
    [
        (
            company_settings.set_brand_style,
            (
                {
                    "heading_font": BrandFont.LORA,
                    "text_font": BrandFont.INTER,
                    "radius": 4,
                    "button_radius": 12,
                },
            ),
        ),
        (company_settings.set_brand_colors, ("dark", None)),
        (company_settings.remove_logo, ()),
    ],
    ids=["style", "colors", "logo"],
)
def test_a_brand_change_whose_log_line_fails_isnt_kept(run, monkeypatch, change, args):
    monkeypatch.setattr(audit, "record", broken)

    async def scenario():
        company, user = await owned()
        before = await transaction(companies.get, company.id)

        with pytest.raises(DatabaseWentAway):
            await change(company, user.uid, *args)

        after = await transaction(companies.get, company.id)
        columns = ("brand_heading_font", "brand_text_font", "brand_radius", "brand_colors")

        return [getattr(row, column) for row in (before, after) for column in columns]

    found = run(scenario())

    assert found[:4] == found[4:]


def test_a_website_whose_log_line_fails_isnt_saved(run, monkeypatch):
    monkeypatch.setattr(audit, "record", broken)

    async def scenario():
        company, user = await owned()

        with pytest.raises(DatabaseWentAway):
            await verification.change_website(company, user, "https://acme.com")

        return (await transaction(companies.get, company.id)).website_domain

    assert run(scenario()) is None
