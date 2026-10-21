import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The home page's info button, beside the demos (under the promise on phones), opens a guide to
// how prepza works in a dialog that closes again.
test("the home page's info button opens its guide", async ({ page }) => {
  // The local dev server compiles the home page on first open.
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  const button = page.getByTestId("page-help").filter({ visible: true });
  await expect(button).toHaveCount(1);
  // An icon alone: its label is what screen readers read.
  await expect(button).toHaveAccessibleName(/.+/);

  // Hovering opens its tooltip (again if the first hover came before the page was ready).
  await expect(async () => {
    await page.mouse.move(0, 0);
    await button.hover();
    await expect(button).toHaveAttribute("data-popup-open", { timeout: 2_000 });
  }).toPass();

  await button.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  // What it's for, then two lists: what to do there, and tips.
  await expect(dialog.getByRole("heading").first()).not.toBeEmpty();
  await expect(dialog.getByRole("list")).toHaveCount(2);

  for (const list of await dialog.getByRole("list").all()) {
    expect(await list.getByRole("listitem").count()).toBeGreaterThan(0);
  }

  await dialog.locator('[data-slot="dialog-footer"] button').click();
  await expect(dialog).toBeHidden();
});
