import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { emailBoxes } from "../helpers/emails"
import { visit, visitUntil } from "../helpers/navigation"
import { uidOf } from "../helpers/sign-in"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// The admin zone is for superadmins only: anyone else finds no such page (a 404, without the
// zone's tabs), the ones that read nothing first (a new template) included, nor the support pages
// about themselves: their own account's and their candidate's, which show none of it.
test("someone who isn't a superadmin finds no admin page", async ({ signInAs }) => {
  const address = ownerEmail()
  const owner = await signInAs(address)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const invite = await api<{ id: string }>(
    owner,
    "POST",
    `/companies/interviews/${interviewId}/candidates`,
    { email: throwawayEmail("candidate") }
  )

  for (const path of [
    "/superadmin/templates/new",
    "/superadmin/stats/general",
    "/superadmin/news",
    "/superadmin/emails",
    "/superadmin/support",
    `/superadmin/support/users/${await uidOf(owner)}`,
    `/superadmin/support/candidates/${invite.id}`,
  ]) {
    await visitUntil(owner, path, 404)
    await expect(owner.locator('a[href="/superadmin/stats/general"]'), path).toHaveCount(0)
    await expect(owner.getByRole("main").locator('a[href="/"]'), path).toBeVisible()
    await expect(owner.getByRole("main").getByRole("textbox"), path).toHaveCount(0)
    await expect(emailBoxes(owner), path).toHaveCount(0)
    await expect(owner.getByRole("main").getByText(address), path).toHaveCount(0)
  }
})

// Questions and stats are tabs with tabs of their own: the old addresses of what moved into them
// open their new places, with the tab and its sub-tab both marked open.
test("the admin zone's older addresses open their tabs' new places", async ({
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  const moved = {
    "/superadmin/questions": "/superadmin/questions/flagged",
    "/superadmin/flagged": "/superadmin/questions/flagged",
    "/superadmin/replaced": "/superadmin/questions/replaced",
    "/superadmin/stats": "/superadmin/stats/general",
    "/superadmin/ai-costs": "/superadmin/stats/ai-costs",
    "/superadmin/emails": "/superadmin/support",
  }

  for (const [from, to] of Object.entries(moved)) {
    await visit(superadmin, from)
    await expect(superadmin, from).toHaveURL(new RegExp(`${to}$`))
    // The side menu marks the moved page, listed under the zone's page it belongs to.
    const open = superadmin.getByRole("main").locator('a[aria-current="page"]:visible')
    await expect(open, from).toHaveCount(1)
    await expect(open, from).toHaveAttribute("href", to)
  }
})
