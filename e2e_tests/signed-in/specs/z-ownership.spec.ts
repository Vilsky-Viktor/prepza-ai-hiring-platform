import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

type Member = { id: string; email: string; role: string; token: string | null }

async function openDeleteAccount(page: Page) {
  await visit(page, "/settings")
  await page.getByTestId("delete-account").click()

  return page.getByRole("dialog")
}

// The owner hands the company to an admin who joined: the admin becomes its owner (told in the
// bell), the owner an admin. Deleting an account waits while it owns a company others joined,
// and names the companies (with their credits) deleted with it; once deleted, what it made in
// other services goes too (accounts' user.deleted: here the API key it made in the company).
test("the owner makes an admin the owner, and an account owning a shared company waits", async ({
  signInAs,
}) => {
  const annEmail = throwawayEmail("owner-ann")
  const bobEmail = throwawayEmail("owner-bob")
  const ann = await signInAs(annEmail)
  const company = await createCompany(ann)
  const own = await createCompany(ann)
  const path = `/companies/members?company_id=${company.id}`
  await api(ann, "POST", path, { email: bobEmail, role: "admin" })
  const [invited] = (await api<Member[]>(ann, "GET", path)).filter(
    (member) => member.email === bobEmail,
  )

  const bob = await signInAs(bobEmail)
  await api(bob, "POST", `/companies/members/invites/${invited.token}/accept`)

  await visit(ann, `/companies/${company.id}/members`)
  const row = ann.getByRole("listitem").filter({ hasText: bobEmail })
  // The row's first button picks the role; "owner" is the menu's last choice.
  await row.getByRole("button").first().click()
  await shot(ann, "owner-choice")
  await ann.getByRole("menu").getByRole("menuitemradio").last().click()
  const dialog = ann.getByRole("dialog")
  await expect(dialog).toContainText(bobEmail)
  await shot(ann, "make-owner")
  await dialog.getByRole("button").last().click()
  await expect(dialog).toHaveCount(0)
  // Bob is the owner, Ann an admin.
  const roles = async () =>
    Object.fromEntries((await api<Member[]>(ann, "GET", path)).map((member) => [member.email, member.role]))
  await expect.poll(roles).toEqual({ [annEmail]: "admin", [bobEmail]: "owner" })
  await shot(ann, "made-owner")

  // Bob hears it in the bell: a notification naming the company.
  await visit(bob, "/companies")
  await expect(async () => {
    await bob.reload()
    await bob.getByTestId("notifications").click()
    await expect(bob.getByRole("menu").getByRole("menuitem").filter({ hasText: company.name })).toBeVisible({
      timeout: 3000,
    })
  }).toPass({ timeout: 60_000 })
  await shot(bob, "bell-owner")

  // Bob owns a company Ann is in: his account waits, the company named with a link to its team.
  const bobDialog = await openDeleteAccount(bob)
  await expect(bobDialog.locator(`a[href$="/companies/${company.id}/members"]`)).toHaveText(company.name)
  await expect(bobDialog.getByRole("button").last()).toBeDisabled()
  await shot(bob, "delete-blocked")

  // Ann owns one company alone: it's named and goes with her account; the one Bob owns isn't.
  const annDialog = await openDeleteAccount(ann)
  await expect(annDialog.getByRole("listitem").filter({ hasText: own.name })).toBeVisible()
  await expect(annDialog.getByText(company.name)).toHaveCount(0)
  await expect(annDialog.getByRole("button").last()).toBeEnabled()
  await shot(ann, "delete-named")

  // Ann, now an admin of Bob's company, made an API key there; deleting her account takes it.
  const keysPath = `/v1/manage/keys?company_id=${company.id}`
  const { id: keyId } = await api<{ id: string }>(ann, "POST", keysPath, {
    name: "Careers site",
    expiry: "1",
    permissions: ["interviews:read"],
  })
  const deleted = ann.waitForResponse(
    (response) => response.url().endsWith("/accounts/me") && response.request().method() === "DELETE",
  )
  await annDialog.getByRole("button").last().click()
  expect((await deleted).status()).toBe(204)
  const keyIds = async () =>
    (await api<{ keys: { id: string }[] }>(bob, "GET", `/v1/manage?company_id=${company.id}`)).keys.map(
      (key) => key.id,
    )
  await expect.poll(keyIds, { timeout: 60_000 }).not.toContain(keyId)
})
