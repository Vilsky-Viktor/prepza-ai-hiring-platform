import { expect, test, type Locator } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's "just ask Mira" section: Mira's chat plays beside three cards, the one the
// chat is showing lit. A lit card's icon takes the lit colour; the others' icons stay muted.

function iconColor(card: Locator) {
  return card.locator("svg").first().evaluate((icon) => getComputedStyle(icon).color);
}

test("the lit card's icon stands out from the others", async ({ page }) => {
  test.setTimeout(120_000);
  await page.clock.install();
  await page.goto("/");
  await loaded(page);
  // Time stands still from here on, moving only as the test runs it, so the lit card stays.
  const now = await page.evaluate(() => Date.now());
  await page.clock.pauseAt(now + 1_000);
  const section = page.locator("#agent");
  await section.scrollIntoViewIfNeeded();
  const cards = section.getByTestId("icon-card");
  await expect(cards).toHaveCount(3);

  await expect
    .poll(
      async () => {
        await page.clock.runFor(250);

        return section.locator("[data-testid=icon-card][data-lit]").count();
      },
      { timeout: 60_000 },
    )
    .toBe(1);
  const lit = section.locator("[data-testid=icon-card][data-lit]");
  const unlit = section.locator("[data-testid=icon-card]:not([data-lit])");
  await expect(unlit).toHaveCount(2);

  // The colours change over a short transition, so they're read until they settle.
  await expect
    .poll(async () => {
      const [first, second] = await Promise.all((await unlit.all()).map(iconColor));
      const shown = await iconColor(lit);

      return first === second && shown !== first;
    })
    .toBe(true);
});
