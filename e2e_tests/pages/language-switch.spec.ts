import { expect, type Page, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The footer's language menu: on a page with versions in other languages, each language is a
// plain link to that page's version, the ones its head names for search engines, named in
// English and sorted, whatever the page's language.

const ENGLISH = new Intl.DisplayNames(["en"], { type: "language", languageDisplay: "standard" });

/** The page's versions as its head names them: hreflang code and path. */
async function versions(page: Page) {
  return page
    .locator('head link[rel="alternate"][hreflang]:not([hreflang="x-default"])')
    .evaluateAll((links) =>
      links.map((link) => ({
        code: link.getAttribute("hreflang")!,
        path: new URL((link as HTMLLinkElement).href).pathname,
      })),
    );
}

for (const [address, own] of [
  ["/pricing", "en"],
  ["/ar/pricing", "ar"],
] as const) {
  test(`the language menu on ${address} lists its versions in English`, async ({ page }) => {
    await page.goto(address);
    const expected = (await versions(page))
      // Filipino's hreflang is Tagalog's code; its name stays Filipino.
      .map((version) => ({ ...version, name: ENGLISH.of(version.code === "tl" ? "fil" : version.code)! }))
      .sort((a, b) => a.name.localeCompare(b.name, "en"));
    expect(expected.length).toBe(23);

    const trigger = page.getByRole("contentinfo").locator('[aria-haspopup="menu"]');
    // The page's own language, in English, is in the button's name.
    await expect(trigger).toHaveAccessibleName(new RegExp(`${ENGLISH.of(own)}$`));
    await trigger.click();
    const items = page.getByRole("menu").getByRole("menuitemradio");
    await expect(items).toHaveCount(expected.length);

    const shown = await items.evaluateAll((links) =>
      links.map((link) => ({
        path: link.getAttribute("href"),
        name: link.textContent?.trim(),
        lang: link.querySelector("[lang]")?.getAttribute("lang"),
      })),
    );
    expect(shown).toEqual(expected.map((version) => ({ path: version.path, name: version.name, lang: "en" })));
    // The page's own language is the one checked.
    const current = page.getByRole("menu").locator(`a[href="${address}"]`);
    await expect(current).toHaveAttribute("aria-checked", "true");
  });
}

test("a language in the menu opens that version of the page", async ({ page }) => {
  await page.goto("/pricing");
  await page.getByRole("contentinfo").locator('[aria-haspopup="menu"]').click();
  await page.getByRole("menu").locator('a[href="/de/pricing"]').click();

  await expect(page).toHaveURL(/\/de\/pricing$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
});

test("a page with one address has no language menu", async ({ page }) => {
  await page.goto("/privacy");
  await loaded(page);

  await expect(page.getByRole("contentinfo").locator('[aria-haspopup="menu"]')).toHaveCount(0);
});
