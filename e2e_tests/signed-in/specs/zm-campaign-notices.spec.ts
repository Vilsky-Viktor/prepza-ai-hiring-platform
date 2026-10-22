import { API_URL } from "../constants"
import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { openDialog, visit } from "../helpers/navigation"
import { tokenOf } from "../helpers/sign-in"
import { ownerEmail, randomId } from "../helpers/users"

type Campaign = {
  id: string
  kind: string
  subject: string
  groups: string[]
  editors_only: boolean
  companies: { id: string; name: string }[]
}

const PATH = "/notifications/superadmin/campaigns"
const NOT_ACKNOWLEDGED =
  "Confirm that this notice is about the service itself, not a promotion, before sending it."

// A superadmin writes an important notice to one company's owners and admins: the audience's
// count is the service's, the audience is saved, and sending needs the box ticked first, which
// the service checks too. Nothing is sent (a notice ignores email settings, and one a day may
// go out): the draft is deleted.
test("superadmin writes an important notice to one company's owners and admins", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const superadmin = await signInSuperadmin()
  const subject = `E2E notice ${randomId()}`

  try {
    await visit(superadmin, "/superadmin/campaigns")
    await openDialog(superadmin, superadmin.getByTestId("new-campaign"))
    const dialog = superadmin.getByRole("dialog")

    // The kind's menu's third choice, then the companies' owners and admins, of this company.
    await dialog.getByRole("button").first().click()
    await superadmin.getByRole("menu").getByRole("menuitemradio").nth(2).click()
    await superadmin.getByTestId("audience-members").click()
    await superadmin.getByTestId("audience-editors-only").click()
    await superadmin.getByTestId("campaign-companies").click()
    await expect(superadmin.getByRole("option").first()).toBeVisible()
    await superadmin.keyboard.type(company.name)
    await superadmin.getByRole("option", { name: company.name }).click()
    await superadmin.keyboard.press("Escape")
    await expect(superadmin.getByTestId("campaign-companies")).toContainText(company.name)

    // The count is what the service counts for this audience: the company's owner.
    const { count } = await api<{ count: number }>(superadmin, "POST", `${PATH}/recipients`, {
      kind: "notices",
      groups: ["members"],
      editors_only: true,
      company_ids: [company.id],
    })
    expect(count).toBe(1)
    await expect(superadmin.getByTestId("audience-count")).toContainText(String(count))

    await dialog.getByRole("textbox").first().fill(subject)
    const editor = dialog.locator("[contenteditable=true]")
    await editor.click()
    await superadmin.keyboard.type("Down on Sunday.")
    await expect(editor).toContainText("Down on Sunday.")
    await dialog.locator("button[type=submit]").click()
    await expect(superadmin).toHaveURL(/\/superadmin\/campaigns\/[0-9a-f-]{36}$/, {
      timeout: 90_000,
    })
    const id = superadmin.url().split("/").pop() ?? ""
    const saved = await api<Campaign>(superadmin, "GET", `${PATH}/${id}`)
    expect([saved.kind, saved.groups, saved.editors_only]).toEqual(["notices", ["members"], true])
    expect(saved.companies).toEqual([{ id: company.id, name: company.name }])
    await expect(superadmin.getByTestId("campaign-companies")).toHaveText(company.name)

    // Sending waits for the box; closed without sending.
    await openDialog(superadmin, superadmin.getByTestId("send-campaign"))
    const confirm = superadmin.getByRole("dialog")
    await expect(confirm.getByRole("button").last()).toBeDisabled()
    await superadmin.getByTestId("notice-acknowledged").click()
    await expect(confirm.getByRole("button").last()).toBeEnabled()
    await superadmin.keyboard.press("Escape")
    await expect(confirm).toBeHidden()

    // The service refuses a notice sent without the confirmation, and says why.
    const refused = await superadmin.request.post(`${API_URL}${PATH}/${id}/send`, {
      headers: { Authorization: `Bearer ${await tokenOf(superadmin)}` },
    })
    expect(refused.status()).toBe(422)
    expect((await refused.json()).detail).toBe(NOT_ACKNOWLEDGED)
  } finally {
    const rows = await api<Campaign[]>(superadmin, "GET", `${PATH}?offset=0&limit=100`)

    for (const row of rows.filter((one) => one.subject === subject)) {
      await api(superadmin, "DELETE", `${PATH}/${row.id}`).catch(() => {})
    }
  }
})
