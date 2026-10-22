import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail } from "../helpers/users"

// An owner rolls a web hook's signing secret: asked first, then the new one, shown once.
test("an owner rolls a web hook's secret and sees the new one once", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const made = await api<{ secret: string }>(
    owner,
    "POST",
    `/v1/manage/webhooks?company_id=${company.id}`,
    { url: "https://example.com/prepza-webhook" }
  )

  await visit(owner, `/companies/${company.id}/integrations/api?tab=webhooks`)
  await shot(owner, "webhooks")
  // The web hook's icon button, named for screen readers.
  await openDialog(owner, owner.getByRole("button", { name: "Roll secret" }))
  await shot(owner, "asked")
  await owner.getByRole("dialog").getByRole("button").last().click()

  const shown = owner.getByRole("dialog")
  await expect(shown.getByText(/^whsec_/)).toBeVisible()
  await expect(shown.getByText(made.secret)).toHaveCount(0)
  await shot(owner, "rolled")
  await owner.setViewportSize(PHONE)
  await shot(owner, "rolled-phone")
})
