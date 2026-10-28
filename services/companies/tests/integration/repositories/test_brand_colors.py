import asyncio
import uuid

from companies.constants.brand import PREPZA_COLORS, Theme
from companies.repositories import companies

MINE = {**PREPZA_COLORS["dark"], "primary": "#ff7a1a"}
LIGHT = {**PREPZA_COLORS["light"], "primary": "#7a1aff"}


def test_each_theme_saves_on_its_own_and_goes_back_to_prepzas_alone(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        # Two people saving the two themes at once both keep theirs.
        await asyncio.gather(
            companies.set_brand_colors(company.id, "dark", MINE),
            companies.set_brand_colors(company.id, "light", LIGHT),
        )
        both = (await companies.get(company.id)).brand_colors
        # As the route passes it: a Theme.
        await companies.set_brand_colors(company.id, Theme.LIGHT, None)
        dark_only = (await companies.get(company.id)).brand_colors

        return both, dark_only

    both, dark_only = run(scenario())

    assert both == {"dark": MINE, "light": LIGHT}
    assert dark_only == {"dark": MINE}
