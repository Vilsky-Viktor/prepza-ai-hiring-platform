import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";

// The pricing page shows the free candidates exactly as billing's catalog gives them (the home
// page's prices: landing.spec.ts).

type Catalog = { free_candidates: number };

async function catalog(page: import("@playwright/test").Page) {
  const response = await page.request.get(`${REQUEST_URL}/api/billing/catalog`);

  return (await response.json()) as Catalog;
}

test("the pricing page shows the catalog's free candidates", async ({ page }) => {
  const prices = await catalog(page);
  await page.goto("/pricing");

  // The price list's second row: the free candidates a new company gets.
  await expect(page.locator("main ul").first().locator("li").nth(1)).toContainText(
    String(prices.free_candidates),
  );
});

// A price row lights up under the pointer, so the eye follows its line to the price.
test("a price row changes its background on hover", async ({ page }, info) => {
  test.skip(info.project.name === "phone", "no hover on a touch screen");
  await page.goto("/pricing");
  const row = page.locator("main ul").first().locator("li").first();
  const background = () => row.evaluate((element) => getComputedStyle(element).backgroundColor);
  const before = await background();

  await row.hover();
  await expect.poll(background).not.toBe(before);
});
