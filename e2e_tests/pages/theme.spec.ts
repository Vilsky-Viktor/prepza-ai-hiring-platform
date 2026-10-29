import { expect, test, type Page } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The site's theme: the device's light or dark setting until a visitor picks one; the header's
// theme buttons (system, light, dark, in that order) keep the choice.

const html = (page: Page) => page.locator("html");
const modes = (page: Page) => page.getByRole("banner").getByRole("group").getByRole("button");

for (const scheme of ["light", "dark"] as const) {
  test(`a new visitor on a ${scheme} device gets the ${scheme} theme`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto("/");
    await loaded(page);

    if (scheme === "dark") {
      await expect(html(page)).toHaveClass(/\bdark\b/);
    } else {
      await expect(html(page)).not.toHaveClass(/\bdark\b/);
    }

    // The header's system button shows as picked.
    await expect(modes(page).first()).toHaveAttribute("aria-pressed", "true");
  });
}

test("a new visitor's theme follows the device when it changes", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await loaded(page);
  await expect(html(page)).not.toHaveClass(/\bdark\b/);

  await page.emulateMedia({ colorScheme: "dark" });
  await expect(html(page)).toHaveClass(/\bdark\b/);
});

test("a visitor who picks dark keeps it on a light device", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await loaded(page);

  await modes(page).nth(2).click();
  await expect(html(page)).toHaveClass(/\bdark\b/);

  await page.reload();
  await loaded(page);
  await expect(modes(page).nth(2)).toHaveAttribute("aria-pressed", "true");
  await expect(html(page)).toHaveClass(/\bdark\b/);
});

test("a visitor who picks light keeps it on a dark device", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto("/");
  await loaded(page);

  await modes(page).nth(1).click();
  await expect(html(page)).not.toHaveClass(/\bdark\b/);

  await page.reload();
  await loaded(page);
  await expect(modes(page).nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(html(page)).not.toHaveClass(/\bdark\b/);
});
