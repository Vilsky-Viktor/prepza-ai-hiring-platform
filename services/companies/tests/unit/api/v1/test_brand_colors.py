import pytest
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.brand import (
    BUTTON_TEXT_UNREADABLE,
    CARD_TEXT_UNREADABLE,
    PAGE_TEXT_UNREADABLE,
    PREPZA_COLORS,
    PRIMARY_UNSEEN,
    SECONDARY_TEXT_UNREADABLE,
)
from companies.helpers.brand import color_sets, contrast, unreadable
from companies.repositories import companies
from tests.unit.api.v1.test_logos import COMPANY_ID, company, sign_in  # noqa: F401 (fixtures)

LIGHT = PREPZA_COLORS["light"]
DARK = PREPZA_COLORS["dark"]
URL = f"/companies/{COMPANY_ID}/brand-colors"


def test_contrast_is_wcags():
    assert contrast("#000000", "#ffffff") == pytest.approx(21)
    assert contrast("#777777", "#777777") == pytest.approx(1)


def test_prepzas_own_colors_read_in_both_themes():
    assert unreadable(LIGHT) is None
    assert unreadable(DARK) is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"foreground": "#eeeeee"}, PAGE_TEXT_UNREADABLE),
        ({"card_foreground": "#f0f0f0"}, CARD_TEXT_UNREADABLE),
        ({"primary_foreground": "#0060c0"}, BUTTON_TEXT_UNREADABLE),
        ({"muted_foreground": "#cccccc"}, SECONDARY_TEXT_UNREADABLE),
        ({"primary": "#f2f2ff", "primary_foreground": "#000000"}, PRIMARY_UNSEEN),
    ],
)
def test_colors_that_make_text_hard_to_read_say_which(changes, message):
    assert unreadable({**LIGHT, **changes}) == message


def test_a_theme_without_colors_of_its_own_is_prepzas():
    mine = {**DARK, "primary": "#ff7a1a"}

    assert color_sets(None) == PREPZA_COLORS
    assert color_sets({"dark": mine}) == {"light": LIGHT, "dark": mine}


@pytest.fixture
def saved(monkeypatch, company):  # noqa: F811
    calls = []

    async def fake_set(session, company_id, theme, colors):
        calls.append((theme, colors))

    monkeypatch.setattr(companies, "set_brand_colors", fake_set)

    return calls


def test_an_admin_saves_one_themes_colors_or_goes_back_to_prepzas(client, saved, audited):
    sign_in("bob")
    mine = {**DARK, "primary": "#ff7a1a"}

    assert client.put(f"{URL}/dark", json={"colors": mine}).status_code == 200
    assert client.put(f"{URL}/light", json={"colors": None}).status_code == 200
    assert saved == [("dark", mine), ("light", None)]
    assert (
        audited
        == [(COMPANY_ID, "bob", AuditAction.BRAND_CHANGED, COMPANY_ID, TargetKind.COMPANY)] * 2
    )


def test_unreadable_colors_and_unknown_themes_save_nothing(client, saved, audited):
    sign_in("bob")
    unreadable_colors = {**LIGHT, "foreground": "#eeeeee"}

    refused = client.put(f"{URL}/light", json={"colors": unreadable_colors})

    assert refused.status_code == 422
    assert refused.json()["detail"] == PAGE_TEXT_UNREADABLE
    assert client.put(f"{URL}/sepia", json={"colors": LIGHT}).status_code == 422
    assert (
        client.put(f"{URL}/light", json={"colors": {**LIGHT, "border": "red"}}).status_code == 422
    )
    assert saved == [] and audited == []


def test_only_owners_and_admins_set_colors(client, saved):
    sign_in("mallory")

    assert client.put(f"{URL}/light", json={"colors": LIGHT}).status_code == 404
    assert saved == []


def test_prepzas_colors_font_and_rounding_are_public(client):
    assert client.get("/brand/prepza").json() == {
        "colors": PREPZA_COLORS,
        "style": {"font": "poppins_geist", "radius": 14, "button_radius": 14},
    }


@pytest.fixture
def styled(monkeypatch, company):  # noqa: F811
    calls = []

    async def fake_set(session, company_id, font, radius, button_radius):
        calls.append((font, radius, button_radius))

    monkeypatch.setattr(companies, "set_brand_style", fake_set)

    return calls


def test_an_admin_sets_the_font_and_rounding_within_their_bounds(client, styled):
    sign_in("bob")

    saved = client.put(
        f"/companies/{COMPANY_ID}/brand-style",
        json={"font": "inter", "radius": 0, "button_radius": 6},
    )

    assert saved.status_code == 200
    assert (
        client.put(
            f"/companies/{COMPANY_ID}/brand-style", json={"font": "comic", "radius": 10}
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/companies/{COMPANY_ID}/brand-style", json={"font": "inter", "radius": 25}
        ).status_code
        == 422
    )
    assert styled == [("inter", 0, 6)]


def test_a_font_no_longer_offered_is_prepzas():
    from types import SimpleNamespace

    from companies.helpers.brand import style_of

    old = SimpleNamespace(brand_font="poppins", brand_radius=4, brand_button_radius=None)

    assert style_of(old) == {"font": "poppins_geist", "radius": 4, "button_radius": 14}
