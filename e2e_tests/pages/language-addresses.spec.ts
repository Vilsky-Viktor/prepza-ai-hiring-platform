import { expect, test } from "@playwright/test";

// A page with language versions is English at its plain address whatever language the visitor
// chose; a page with one address (the legal pages) follows the chosen language, and its links
// lead to that language's versions.
test("a plain address stays English after another language was chosen", async ({ page }) => {
  // A first visit through the German address keeps German as the chosen language.
  await page.goto("/de/pricing");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");

  await page.goto("/pricing");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("contentinfo").locator('a[href="/faq"]')).toHaveCount(1);

  await page.goto("/privacy");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  const footer = page.getByRole("contentinfo");
  await expect(footer.locator('a[href="/de/faq"]')).toHaveCount(1);
  await expect(footer.locator('a[href="/faq"]')).toHaveCount(0);
});
