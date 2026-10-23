import { expect, test, type Page } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The site's theme: dark until a visitor picks one, whatever their device's setting; the header's
// theme buttons (system, light, dark, in that order) keep the choice, and "system" follows the
// device.

const html = (page: Page) => page.locator("html");
const modes = (page: Page) => page.getByRole("banner").getByRole("group").getByRole("button");

test("a new visitor gets the dark theme whatever their device says", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await loaded(page);

  await expect(html(page)).toHaveClass(/\bdark\b/);

  // The header's dark button shows as picked (the buttons are hidden on phones).
  if (test.info().project.name !== "phone") {
    await expect(modes(page).nth(2)).toHaveAttribute("aria-pressed", "true");
  }
});

test("a visitor who picks system follows their device, and the choice stays", async ({ page }) => {
  test.skip(test.info().project.name === "phone", "the theme buttons are hidden on phones");
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await loaded(page);
  await expect(html(page)).toHaveClass(/\bdark\b/);

  await modes(page).first().click();
  await expect(modes(page).first()).toHaveAttribute("aria-pressed", "true");
  await expect(html(page)).not.toHaveClass(/\bdark\b/);

  await page.emulateMedia({ colorScheme: "dark" });
  await expect(html(page)).toHaveClass(/\bdark\b/);

  // Kept on the next visit: still the device's setting, not the dark default.
  await page.emulateMedia({ colorScheme: "light" });
  await page.reload();
  await loaded(page);
  await expect(modes(page).first()).toHaveAttribute("aria-pressed", "true");
  await expect(html(page)).not.toHaveClass(/\bdark\b/);
});

test("a visitor who picks light keeps it on a dark device", async ({ page }) => {
  test.skip(test.info().project.name === "phone", "the theme buttons are hidden on phones");
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
