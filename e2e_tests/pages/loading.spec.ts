import { expect, test } from "@playwright/test";

// A page whose data is slow shows the site's frame and a spinner at once, then its content.
test("a slow page shows its loading state first, then the page", async ({ page }) => {
  await page.goto("/pricing");
  const footer = page.getByRole("contentinfo");
  await expect(footer).toBeVisible();

  // The next page's data is held until the spinner has been seen.
  let release = () => {};
  const held = new Promise<void>((resolve) => (release = resolve));
  await page.route(/\/faq\?_rsc=/, async (route) => {
    await held;
    await route.continue();
  });
  await footer.locator('a[href="/faq"]').click();

  const main = page.getByRole("main");
  await expect(main.getByRole("status")).toBeVisible();
  // The header and footer stay while it loads.
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(footer).toBeVisible();

  release();
  await expect(page).toHaveURL(/\/faq$/);
  await expect(main.getByRole("status")).toHaveCount(0);
  await expect(main.getByRole("heading", { level: 1 })).toBeVisible();
});
