import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The contact form shows no labels, only placeholders, so each field carries its own accessible
// name, which stays once something is typed (a placeholder alone would vanish).
test("each contact field keeps its accessible name, also once filled", async ({ page }) => {
  await page.goto("/contact");
  await loaded(page);
  const form = page.getByRole("main").locator("form");
  const fields = form.getByRole("textbox");
  await expect(fields).toHaveCount(3);
  await expect(form.locator("label")).toHaveCount(0);

  for (const field of await fields.all()) {
    await field.fill("Anna Kowalska");
    await expect(field).toHaveAccessibleName(/\S/);
  }
});
