import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { deleteTemplate } from "../helpers/db-library"
import {
  addPracticeResult,
  deletePracticeResults,
  markPaid,
  matchingTemplate,
  openToOffers,
  unmarkPaid,
} from "../helpers/discover"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { tokenOf, uidOf } from "../helpers/sign-in"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

type Candidate = { email: string }

// A company that has topped up sees, on an interview's Discover tab, the people open to offers
// who practised its subjects: their name with their LinkedIn profile, and their practice result
// on each matching subject. An owner invites one as any candidate, at their account's email.
test("a paying company finds a talent on Discover and invites them", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  await markPaid(company.id)
  const interviewId = await createInterview(owner, company.id)
  const { templateId, topicId } = await matchingTemplate(owner, interviewId)
  const name = `E2E Talent ${randomId()}`
  const email = throwawayEmail("discover")
  const talent = await signInAs(email, undefined, name)
  const talentId = await uidOf(talent)
  const profile = `https://www.linkedin.com/in/e2e-${randomId()}`

  try {
    await addPracticeResult(talentId, templateId, topicId, 80)
    await openToOffers(talent, profile)

    const interviewPath = `/companies/${company.id}/interviews/${interviewId}`
    await visit(owner, interviewPath)
    // The tab is in the interview's menu.
    await expect(
      owner.getByRole("main").getByRole("navigation").locator('a[href$="?tab=discover"]').first()
    ).toBeAttached()
    await visit(owner, `${interviewPath}?tab=discover`)
    const linkedin = owner.getByRole("link", { name: new RegExp(name) })
    const row = owner.getByTestId("discover-row").filter({ visible: true }).filter({ has: linkedin })
    await expect(row).toHaveCount(1)
    await expect(linkedin).toHaveAttribute("href", profile)
    // The practice result on the matching subject.
    await expect(row.getByRole("listitem")).toHaveCount(1)
    await expect(row.getByRole("listitem")).toContainText("80%")
    await shot(owner, "discover")

    // Invite: a success toast, and they're among the candidates at their account's email.
    await row.getByRole("button").click()
    await expect(owner.locator('[data-sonner-toast][data-type="success"]')).toContainText(name)
    await expect(row.getByRole("button")).toBeDisabled()
    const candidates = await api<Candidate[]>(
      owner,
      "GET",
      `/companies/interviews/${interviewId}/candidates?sort=date`
    )
    expect(candidates.map((candidate) => candidate.email)).toContain(email)
  } finally {
    await api(talent, "DELETE", "/rounds/open-to-offers")
    await deletePracticeResults(talentId, templateId)
    await deleteTemplate(templateId)
    await unmarkPaid(company.id)
  }
})

// A company that never topped up has no Discover tab, and the API refuses it the list, so
// throwaway sign-ups never see people's details.
test("a company that never topped up has no Discover", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const interviewPath = `/companies/${company.id}/interviews/${interviewId}`

  await visit(owner, `${interviewPath}?tab=discover`)
  // The topics tab shows instead, with no Discover in the menu.
  await expect(owner.getByRole("main").getByRole("navigation").first()).toBeVisible()
  await expect(owner.locator('a[href$="?tab=discover"]')).toHaveCount(0)

  const response = await owner.request.get(
    `${API_URL}/companies/interviews/${interviewId}/discover`,
    { headers: { Authorization: `Bearer ${await tokenOf(owner)}` } }
  )
  expect(response.status()).toBe(403)
  expect((await response.json()).code).toBe("discover_unpaid")
})
