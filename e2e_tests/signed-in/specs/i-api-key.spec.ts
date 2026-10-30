import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { api, createCompany } from "../helpers/api"
import { permissionTicks } from "../helpers/api-keys"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// The API's refusal of a range with bits set after its prefix, naming the entry.
const BAD_RANGE = "203.0.113.7/24 isn't an IP address or a range like 203.0.113.0/24"
// Pydantic's refusal of a key left with no permission.
const NO_PERMISSION = "List should have at least 1 item after validation, not 0"

// A key's own page: its permissions change at once both ways (a refused change is undone), and
// its allowed IPs are added and taken off; the API follows both. Then it's deleted from there.
test("an owner changes a key's permissions and allowed IPs on its page", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const { key } = await api<{ key: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    { name: "Careers site", expiry: "1", permissions: ["interviews:read"] }
  )
  const headers = { Authorization: `Bearer ${key}` }
  const credits = () => owner.request.get(`${API_URL}/v1/credits`, { headers })
  const apiPage = `/companies/${company.id}/integrations/api`

  await owner.setViewportSize({ width: 1280, height: 1200 })
  await visit(owner, apiPage)
  await owner.getByRole("main").getByRole("link", { name: "Careers site" }).click()
  await expect(owner).toHaveURL(/\/integrations\/api\/keys\/[0-9a-f-]+$/)
  const keyPage = new URL(owner.url()).pathname
  await expect(owner.getByRole("heading", { level: 1 })).toHaveText("Careers site")

  // "Select all", then every permission the API lists: only interviews read ticked.
  const form = owner.getByRole("main")
  const { all: ticks, count, tick } = await permissionTicks(owner, company.id, form)
  const checked = owner.getByRole("main").locator('[role=checkbox][aria-checked="true"]')
  const success = owner.locator('[data-sonner-toast][data-type="success"]')
  const error = owner.locator('[data-sonner-toast][data-type="error"]')
  await expect(ticks).toHaveCount(count)
  await expect(checked).toHaveCount(1)
  await expect(tick("interviews:read")).toBeChecked()
  await shot(owner, "key-page")

  // Credits read ticked: saved at once, kept after a reload, and the key reads the credits.
  expect((await credits()).status()).toBe(403)
  await tick("credits:read").click()
  await expect(success).toBeVisible()
  await visit(owner, keyPage)
  await expect(tick("credits:read")).toBeChecked()
  await expect(checked).toHaveCount(2)
  expect((await credits()).status()).toBe(200)

  // And unticked again: the key can't any more.
  await tick("credits:read").click()
  await expect(success).toBeVisible()
  await visit(owner, keyPage)
  await expect(tick("credits:read")).not.toBeChecked()
  await expect(checked).toHaveCount(1)
  expect((await credits()).status()).toBe(403)

  // Its last permission can't go: refused with the API's reason, and the tick comes back.
  await tick("interviews:read").click()
  await expect(error).toHaveText(NO_PERMISSION)
  await expect(tick("interviews:read")).toBeChecked()
  await shot(owner, "permission-refused")
  await visit(owner, keyPage)
  await expect(tick("interviews:read")).toBeChecked()

  // Allowed IPs: a range that isn't clean is refused with the API's reason and stays in the field.
  const field = owner.getByRole("main").getByRole("textbox")
  const add = owner.getByRole("main").locator('form button[type="submit"]')
  const entries = owner.getByTestId("allowed-entry")
  await expect(entries).toHaveCount(0)
  await field.fill("203.0.113.7/24")
  await add.click()
  await expect(error.filter({ hasText: BAD_RANGE })).toBeVisible()
  await expect(field).toHaveValue("203.0.113.7/24")
  await expect(entries).toHaveCount(0)

  // A range and an IPv6 address (kept in its shortest form), added with the button and Enter.
  await field.fill("203.0.113.0/24")
  await add.click()
  await expect(entries).toHaveText(["203.0.113.0/24"])
  await expect(field).toHaveValue("")
  await field.fill("2001:db8:0:0::1")
  await field.press("Enter")
  await expect(entries).toHaveText(["203.0.113.0/24", "2001:db8::1"])
  await shot(owner, "ips-added")
  // A call from anywhere else is refused.
  const refused = await credits()
  expect(refused.status()).toBe(403)
  expect((await refused.json()).code).toBe("ip_not_allowed")
  await visit(owner, keyPage)
  await expect(entries).toHaveText(["203.0.113.0/24", "2001:db8::1"])

  // Both taken off: any address may use it again.
  await entries.first().getByRole("button").click()
  await expect(entries).toHaveText(["2001:db8::1"])
  await entries.first().getByRole("button").click()
  await expect(entries).toHaveCount(0)
  await visit(owner, keyPage)
  await expect(entries).toHaveCount(0)
  expect((await credits()).status()).toBe(403)
  expect((await (await credits()).json()).code).toBe("missing_permission")

  // On a phone the columns stack.
  await owner.setViewportSize(PHONE)
  await shot(owner, "key-page-phone")

  // Deleted from its page: back to the API page, where it's gone.
  await openDialog(owner, owner.getByRole("button", { name: "Delete key" }))
  await owner.getByRole("dialog").getByRole("button").last().click()
  await expect(owner).toHaveURL(new RegExp(`${apiPage}$`))
  await expect(owner.getByRole("main").getByRole("link", { name: "Careers site" })).toHaveCount(0)
  expect((await credits()).status()).toBe(401)
})

// A viewer sees a key's permissions and allowed IPs, with nothing to change.
test("a viewer sees a key's page without changing it", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const { id } = await api<{ id: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    {
      name: "Dashboard",
      expiry: "1",
      permissions: ["interviews:read"],
      allowed_ips: ["203.0.113.0/24"],
    }
  )
  const viewerAddress = ownerEmail()
  const invited = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewerAddress, role: "viewer" }
  )
  const viewer = await signInAs(viewerAddress)
  await api(viewer, "POST", `/companies/members/invites/${invited.token}/accept`)

  await visit(viewer, `/companies/${company.id}/integrations/api/keys/${id}`)
  await expect(viewer.getByRole("heading", { level: 1 })).toHaveText("Dashboard")
  await expect(viewer.getByTestId("key-permissions").locator("[data-slot=badge]")).toHaveCount(1)
  await expect(viewer.getByTestId("allowed-entry")).toHaveText(["203.0.113.0/24"])
  await expect(viewer.getByRole("main").getByRole("checkbox")).toHaveCount(0)
  await expect(viewer.getByRole("main").getByRole("textbox")).toHaveCount(0)
  await expect(viewer.getByTestId("allowed-entry").getByRole("button")).toHaveCount(0)
  await expect(viewer.getByRole("button", { name: "Delete key" })).toHaveCount(0)
  await shot(viewer, "viewer")
})
