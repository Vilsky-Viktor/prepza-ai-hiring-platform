# The company fixture is imported from the AI apps tests and named in the tests.
# ruff: noqa: F811
from testee_common.i18n.i18n import translate

from companies.constants.brand import QUESTION_TEXT_UNREADABLE, TESTEE_COLORS
from tests.unit.api.v1.test_ai_apps import COMPANY_ID, company, sign_in  # noqa: F401
from tests.unit.api.v1.test_brand_colors import SAVED_BEFORE

MINE = {**TESTEE_COLORS["dark"], "primary": "#ff7a1a"}


def test_saved_colors_a_check_now_refuses_stay_in_settings_with_why(client, company):
    company.brand_colors = {"light": SAVED_BEFORE, "dark": MINE}

    shown = client.get(f"/companies/{COMPANY_ID}", headers={"Accept-Language": "de"}).json()

    # The settings keep the company's own colors to adjust; its candidates see testee's.
    assert shown["brand_colors"] == {"light": SAVED_BEFORE, "dark": MINE}
    assert shown["candidate_colors"] == {"light": TESTEE_COLORS["light"], "dark": MINE}
    assert shown["brand_problems"] == {"light": translate(QUESTION_TEXT_UNREADABLE, "de")}


def test_colors_that_read_have_no_problems(client, company):
    company.brand_colors = {"dark": MINE}

    assert client.get(f"/companies/{COMPANY_ID}").json()["brand_problems"] == {}
