import { expect, test } from "@playwright/test";

import { REQUEST_URL } from "./helpers/env";
import { loaded } from "./helpers/waits";

// Every published version of a legal document stays readable at its own address, and each says
// whether it applies, with a link to the one in force when it doesn't. Versions are checked by
// the API's version dates in the addresses.
type Legal = { current: string; in_force: string; versions: string[] };

/** A version's address: the current one's is the plain one. */
function address(legal: Legal, version: string) {
  return version === legal.current ? "/terms" : `/terms?version=${version}`;
}

test("the terms show when they apply and keep every earlier version", async ({ page }) => {
  const legal: Legal = await (
    await page.request.get(`${REQUEST_URL}/api/rounds/help/legal/terms`)
  ).json();
  await page.goto("/terms");
  await loaded(page);
  const header = page.locator("main header");
  // Dates as the language writes them, not as the API names them.
  await expect(header).toContainText(/[A-Z][a-z]{2} \d{1,2}, \d{4}/);

  // A version published ahead of its day links to the one in force until then.
  if (legal.current !== legal.in_force) {
    await page.screenshot({ path: test.info().outputPath("terms-ahead.png") });
    await header.locator(`a[href="${address(legal, legal.in_force)}"]`).click();
    await expect(page).toHaveURL(new RegExp(`/terms\\?version=${legal.in_force}$`));
  }

  // The version in force needs no link onwards.
  await expect(header.locator("a")).toHaveCount(0);
  await page.screenshot({ path: test.info().outputPath("terms.png"), fullPage: true });
  // Every other version, linked by its date.
  const links = page.locator("main nav a");
  const hrefs = await links.evaluateAll((items) => items.map((item) => item.getAttribute("href")));
  expect(hrefs).toEqual(
    legal.versions.filter((version) => version !== legal.in_force).map((version) => address(legal, version)),
  );

  // An earlier version says it was replaced, with a link to the one in force.
  const old = legal.versions.find((version) => version !== legal.current && version !== legal.in_force);
  expect(old).toBeDefined();
  await page.locator(`main nav a[href="/terms?version=${old}"]`).click();
  await expect(page).toHaveURL(new RegExp(`/terms\\?version=${old}$`));
  await page.screenshot({ path: test.info().outputPath("terms-old.png") });

  await header.locator(`a[href="${address(legal, legal.in_force)}"]`).click();
  await expect(page).toHaveURL(/\/terms(\?version=[\d-]+)?$/);
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
  await page.screenshot({ path: test.info().outputPath("terms-de.png") });

  await header.locator('a[href="/terms?language=en"]').click();
  await expect(page).toHaveURL(/\/terms\?language=en$/, { timeout: 15_000 });
  await expect(text).toHaveAttribute("lang", "en");

  await page.context().addCookies([{ name: "prepza_locale", value: "ar", url: baseURL! }]);
  await page.goto("/privacy");
  await expect(text).toHaveAttribute("dir", "rtl");
  await page.screenshot({ path: test.info().outputPath("privacy-ar.png") });
});
