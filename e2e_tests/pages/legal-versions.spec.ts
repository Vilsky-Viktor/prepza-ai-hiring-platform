import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { shot } from "./helpers/screenshots";
import { loaded } from "./helpers/waits";

// The terms in force: the page says since when, with no link to another version, and its
// versions card links every other published version (none while there's just one). Versions are
// checked by the API's version dates in the addresses.
type Legal = { current: string; in_force: string; versions: string[] };

test("the terms show since when they apply", async ({ page }) => {
  const legal: Legal = await (
    await page.request.get(`${REQUEST_URL}/api/site/help/legal/terms`)
  ).json();
  expect(legal.in_force).toBe(legal.current);
  await page.goto("/terms");
  await loaded(page);
  const header = page.locator("main header");
  // Dates as the language writes them, not as the API names them.
  await expect(header).toContainText(/[A-Z][a-z]{2} \d{1,2}, \d{4}/);
  // The version in force needs no link onwards to another version.
  await expect(header.locator('a[href*="version="]')).toHaveCount(0);
  await shot(page, "terms", true);
  // The versions card, with every other version linked by its date.
  await expect(page.locator("main nav")).toHaveCount(1);
  const hrefs = await page
    .locator("main nav a")
    .evaluateAll((items) => items.map((item) => item.getAttribute("href")));
  expect(hrefs).toEqual(
    legal.versions.filter((version) => version !== legal.current).map((version) => `/terms?version=${version}`),
  );
});

// Each document in the page's language, with a link to the binding English.
test("the terms show in the page's language with a link to the binding English", async ({ page, baseURL }) => {
  await page.context().addCookies([{ name: "prepza_locale", value: "de", url: baseURL! }]);
  await page.goto("/terms");
  await loaded(page);
  const text = page.locator("main div[lang]");
  await expect(text).toHaveAttribute("lang", "de");
  // Dates as German writes them.
  const header = page.locator("main header");
  await expect(header).toContainText(/\d{2}\.\d{2}\.\d{4}/);
  await shot(page, "terms-de");

  await header.locator('a[href="/terms?language=en"]').click();
  await expect(page).toHaveURL(/\/terms\?language=en$/, { timeout: 15_000 });
  await expect(text).toHaveAttribute("lang", "en");

  await page.context().addCookies([{ name: "prepza_locale", value: "ar", url: baseURL! }]);
  await page.goto("/privacy");
  await expect(text).toHaveAttribute("dir", "rtl");
  await shot(page, "privacy-ar");
});
