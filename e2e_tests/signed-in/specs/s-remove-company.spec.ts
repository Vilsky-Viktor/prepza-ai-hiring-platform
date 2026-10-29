import type { Page } from "@playwright/test";

import { expect, test } from "../fixtures";
import { api, createCompany } from "../helpers/api";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

/** The Remove button on a company's row in the companies list, the row's one button. */
function removeButton(page: Page, companyId: string) {
  return page
    .getByRole("listitem")
    .filter({ has: page.locator(`a[href="/companies/${companyId}/interviews"]`) })
    .getByRole("button");
}

// Removing a company deletes its credits: the dialog says how many are lost (and the
// candidates they'd pay for) when there are any, and nothing about credits otherwise.
test("removing a company warns about the credits it loses", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  // A first company gets the welcome credits (billing's catalog says how many, and for how many
  // candidates); a second one none.
  const catalog = await api<{ welcome_company: number; free_candidates: number }>(
    owner,
    "GET",
    "/billing/catalog",
  );
  const funded = await createCompany(owner);
  const empty = await createCompany(owner);
  await visit(owner, "/companies");

  await removeButton(owner, funded.id).click();
  let dialog = owner.getByRole("dialog");
  const credits = dialog.getByTestId("remove-credits");
  await expect(credits).toContainText(catalog.welcome_company.toLocaleString("en-US"));
  await expect(credits).toContainText(String(catalog.free_candidates));
  await shot(owner, "remove-with-credits");
  // Cancel, then Remove.
  await dialog.getByRole("button").first().click();
  await expect(dialog).toHaveCount(0);

  await removeButton(owner, empty.id).click();
  dialog = owner.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByTestId("remove-credits")).toHaveCount(0);

  // Removed, it's gone from the list.
  await dialog.getByRole("button").last().click();
  await expect(owner.getByText(empty.name)).toHaveCount(0);
  await expect(owner.getByText(funded.name).filter({ visible: true })).toBeVisible();
});
