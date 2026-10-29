import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { throwawayEmail } from "../helpers/users"

test.setTimeout(240_000)

// Deleting an interview past the first page (20) takes it off the list at once, and the
// list goes on loading from the right place.
/** A company with 22 interviews, "E2E 01" to "E2E 22": oldest first, so "E2E 01" is last in
 * the list, on its second page. */
async function longList(owner: Page) {
  const company = await createCompany(owner)

  for (let index = 1; index <= 22; index += 1) {
    const id = await createInterview(owner, company.id)
    const title = `E2E ${String(index).padStart(2, "0")}`
    await api(owner, "PATCH", `/companies/interviews/${id}/title`, { title })
  }

  return company
}

test("an interview deleted past the first page leaves the list at once", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("long-list"))
  const company = await longList(owner)

  await visit(owner, `/companies/${company.id}/interviews`)
  await expect(owner.getByText("E2E 22").filter({ visible: true })).toBeVisible()
  // The oldest's row; its last button deletes it.
  const oldest = owner
    .getByRole("main")
    .getByRole("listitem")
    .filter({ hasText: "E2E 01" })
    .getByRole("button")
    .last()
  await expect(async () => {
    await owner.mouse.wheel(0, 4000)
    await expect(oldest).toBeVisible({ timeout: 1000 })
  }).toPass({ timeout: 30_000 })

  await oldest.click()
  await owner.getByRole("dialog").getByRole("button").last().click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  await expect(owner.getByText("E2E 01", { exact: true })).toHaveCount(0)
  await expect(owner.getByText("E2E 02", { exact: true }).filter({ visible: true })).toBeVisible()
})

// A page that fails to load (here the load balancer's own 503 page) says so in an error toast
// whose button tries again, and the list still loads the rest.
test("a page that fails to load can be tried again", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("long-list-retry"))
  const company = await longList(owner)
  let failing = true
  await owner.route("**/api/companies/interviews?*offset=20*", (route) =>
    failing
      ? route.fulfill({ status: 503, contentType: "text/html", body: "<h1>Service Unavailable</h1>" })
      : route.continue()
  )

  const failed = owner.locator('[data-sonner-toast][data-type="error"]').first()
  await visit(owner, `/companies/${company.id}/interviews`)
  await expect(owner.getByText("E2E 22").filter({ visible: true })).toBeVisible()
  await expect(async () => {
    await owner.mouse.wheel(0, 4000)
    await expect(failed).toContainText("Couldn't load more. Please try again.", { timeout: 1000 })
  }).toPass({ timeout: 30_000 })
  await expect(owner.getByText("E2E 01", { exact: true })).toHaveCount(0)

  failing = false
  await failed.locator("[data-button]").click()
  await expect(async () => {
    await owner.mouse.wheel(0, 4000)
    await expect(owner.getByText("E2E 01", { exact: true }).filter({ visible: true })).toBeVisible({ timeout: 1000 })
  }).toPass({ timeout: 30_000 })
})
