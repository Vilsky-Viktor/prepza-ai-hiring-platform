import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// The contact form shows each field's name above it (WCAG 3.3.2: a placeholder alone vanishes
// once something is typed), and that visible label is what names the field.
test("each contact field is named by its visible label, also once filled", async ({ page }) => {
  await page.goto("/contact");
  await loaded(page);
  const fields = page.getByRole("main").getByRole("textbox");
  await expect(fields).toHaveCount(3);

  for (const field of await fields.all()) {
    await field.fill("Anna Kowalska");
    const label = await field.evaluate(
      (element: HTMLInputElement) => element.labels?.[0]?.innerText.trim() ?? "",
    );
    expect(label).not.toBe("");
    await expect(field).toHaveAccessibleName(label);
    await expect(page.getByText(label, { exact: true })).toBeVisible();
  }
});
