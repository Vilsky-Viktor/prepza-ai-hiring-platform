import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The footer's language menu: on a page with versions in other languages, each language is a
// plain link to that page's version, the ones its head names for search engines.
test("the footer's language menu links to the page's language versions", async ({ page }) => {
  await page.goto("/pricing");
  const versions = await page
    .locator('head link[rel="alternate"][hreflang]:not([hreflang="x-default"])')
    .evaluateAll((links) => links.map((link) => new URL((link as HTMLLinkElement).href).pathname));
  expect(versions.length).toBe(23);

  const menuButton = page.getByRole("contentinfo").locator('[aria-haspopup="menu"]');
  await menuButton.click();
  const menu = page.getByRole("menu");
  const items = menu.getByRole("menuitemradio");
  await expect(items).toHaveCount(versions.length);
  expect(
    (await items.evaluateAll((links) => links.map((link) => link.getAttribute("href")))).sort(),
  ).toEqual([...versions].sort());
  // The page's own language is the one checked.
  await expect(menu.locator('a[href="/pricing"]')).toHaveAttribute("aria-checked", "true");

  await menu.locator('a[href="/de/pricing"]').click();
  await expect(page).toHaveURL(/\/de\/pricing$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
});

test("a page with one address has no language menu", async ({ page }) => {
  await page.goto("/privacy");
  await loaded(page);

  await expect(page.getByRole("contentinfo").locator('[aria-haspopup="menu"]')).toHaveCount(0);
});
