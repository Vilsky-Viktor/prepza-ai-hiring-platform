import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId } from "../helpers/users"

/** The superadmin's row for this test's company: the only one the test decides on. */
async function requestRow(superadmin: Page, name: string) {
  await visit(superadmin, "/superadmin/verification")

  return superadmin.getByRole("listitem").filter({ hasText: name })
}

// Verification: a website on the owner's own email domain goes for review; the superadmin
// declines it, a rename sends it again, and the superadmin approves it.
test("company verification: pending, declined, renamed, approved", async ({
  signInAs,
  signInSuperadmin,
}) => {
  // A throwaway domain that isn't a free mail service, with the owner's email on it.
  const domain = `e2e-${randomId()}.test`
  const owner = await signInAs(ownerEmail(domain))
  const company = await createCompany(owner)
  const interviews = `/companies/${company.id}/interviews`
  await visit(owner, interviews)

  const verify = owner.getByTestId("verify-company")
  await verify.click()
  await owner.getByRole("dialog").getByRole("textbox").fill(domain)
  await shot(owner, "verify-dialog")
  await owner.getByRole("dialog").locator('button[type="submit"]').click()
  // The way to verify becomes the pending badge, an icon named for screen readers, with its
  // tooltip on hover.
  const pending = owner.getByRole("button", { name: "Pending verification" })
  await expect(pending).toBeVisible()
  await expect(verify).toHaveCount(0)
  await pending.hover()
  await expect(pending).toHaveAttribute("data-popup-open")
  await shot(owner, "pending")

  const superadmin = await signInSuperadmin()
  // Waiting for review: Decline and Approve, in that order.
  let row = await requestRow(superadmin, company.name)
  await expect(row.getByText(domain)).toBeVisible()
  await expect(row.getByRole("button")).toHaveCount(2)
  await shot(superadmin, "superadmin-pending")
  await row.getByRole("button").first().click()
  const reason = "E2E: the website doesn't match the name."
  await superadmin.getByRole("dialog").getByRole("textbox").fill(reason)
  await shot(superadmin, "decline-dialog")
  await superadmin.getByRole("dialog").locator('button[type="submit"]').click()
  // Decided: nothing left to choose, and the reason with it.
  await expect(row.getByRole("button")).toHaveCount(0)
  await expect(row.getByText(reason)).toBeVisible()
  await shot(superadmin, "superadmin-declined")

  // The company sees why, in the verify dialog.
  await visit(owner, interviews)
  await expect(pending).toHaveCount(0)
  await verify.click()
  await expect(owner.getByRole("dialog").getByText(`Declined: ${reason}`)).toBeVisible()
  await shot(owner, "declined")
  await owner.keyboard.press("Escape")

  // A rename (the title's pencil, named for screen readers) sends it for review again.
  const renamed = `${company.name} Renamed`
  await owner.getByRole("heading").getByRole("button", { name: "Edit title" }).click()
  // The title's field, before the interviews' search.
  const title = owner.getByRole("main").getByRole("textbox").first()
  await shot(owner, "rename-hint")
  await title.fill(renamed)
  await title.press("Enter")
  await expect(owner.getByRole("heading", { name: renamed })).toBeVisible()
  await visit(owner, interviews)
  await expect(pending).toBeVisible()
  await shot(owner, "pending-again")

  row = await requestRow(superadmin, renamed)
  await expect(row.getByRole("button")).toHaveCount(2)
  await row.getByRole("button").last().click()
  await expect(row.getByRole("button")).toHaveCount(0)
  await shot(superadmin, "superadmin-approved")

  await visit(owner, interviews)
  await expect(owner.getByRole("img", { name: `Verified: \u2068${domain}\u2069` })).toBeVisible()
  await shot(owner, "verified")
})
