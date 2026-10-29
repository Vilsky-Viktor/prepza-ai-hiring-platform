import { expect, test } from "@playwright/test";

import { loaded, settled } from "./helpers/waits";

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

// Every guide ends with a card across the whole dialog asking for problems, ideas and missing
// features, whose button opens the contact page.
test("the guide's feedback card leads to the contact page", async ({ page }) => {
  // The local dev server compiles the home page and the contact page on first open.
  test.setTimeout(120_000);
  await page.goto("/");
  await loaded(page);
  await page.getByTestId("page-help").filter({ visible: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await settled(dialog);

  const card = dialog.getByTestId("page-help-feedback");
  await expect(card).toBeVisible();
  // Edge to edge: as wide as the dialog's body, its padding left out.
  const [width, bodyWidth] = await card.evaluate((element) => [
    element.getBoundingClientRect().width,
    element.parentElement!.clientWidth,
  ]);
  expect(Math.round(width)).toBe(bodyWidth);

  const link = card.getByRole("link");
  await expect(link).toHaveCount(1);
  await expect(link).toHaveAccessibleName(/.+/);
  await link.click();
  await expect(page).toHaveURL(/\/contact$/);
  await expect(dialog).toBeHidden();
});
