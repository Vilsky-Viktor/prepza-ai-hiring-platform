import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

/** Follows the generation page of the interview until it's ready: its generation answers as
 * done at once, as a finished one does. */
async function finishGeneration(page: Page, companyId: string, interviewId: string) {
  await page.route(`**/api/companies/interviews/${interviewId}/generation`, (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: interviewId,
        kind: "interview",
        company_id: companyId,
        status: "done",
        topics: null,
        progress: null,
        preparation_id: null,
        error: null,
        language: "en",
        max_topics: 0,
        max_subtopics: 0,
      }),
    })
  )
  await visit(page, `/generate/${interviewId}?next=/companies/${companyId}/interviews/${interviewId}`)
}

// Right after an interview is generated, its page shows what to do next, each step taking the
// user there; closing it takes the mark off the address, so a reload doesn't show it again.
test("a just generated interview shows what to do next", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("whats-next"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const { title } = await api<{ title: string }>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}`
  )
  const interviewPath = `/companies/${company.id}/interviews/${interviewId}`
  const dialog = owner.getByTestId("whats-next")
  const steps = dialog.getByRole("listitem")

  // The generation page brings the user to the interview, marked as just generated.
  await finishGeneration(owner, company.id, interviewId)
  await expect(owner).toHaveURL(new RegExp(`${interviewPath}\\?ready=1$`))
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText(title)
  await expect(steps).toHaveCount(3)
  await shot(owner, "dialog")

  // The first step closes it and puts the cursor in the first topic's question count.
  await steps.nth(0).getByRole("button").click()
  await expect(dialog).toBeHidden()
  await expect(owner).toHaveURL(new RegExp(`${interviewPath}$`))
  await expect(owner.locator("[data-topic-limit]").first()).toBeFocused()
  // Without the mark, a reload doesn't show it.
  await owner.reload()
  await expect(owner.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(dialog).toHaveCount(0)

  // The second opens the settings, the third the candidates.
  await visit(owner, `${interviewPath}?ready=1`)
  await steps.nth(1).getByRole("link").click()
  await expect(owner).toHaveURL(new RegExp(`${interviewPath}\\?tab=settings$`))
  await expect(dialog).toBeHidden()
  await visit(owner, `${interviewPath}?ready=1`)
  await steps.nth(2).getByRole("link").click()
  await expect(owner).toHaveURL(new RegExp(`${interviewPath}\\?tab=candidates$`))
  await expect(dialog).toBeHidden()

  // Its own button closes it too, taking the mark off.
  await visit(owner, `${interviewPath}?ready=1`)
  await dialog.locator('[data-slot="dialog-footer"]').getByRole("button").click()
  await expect(dialog).toBeHidden()
  await expect(owner).toHaveURL(new RegExp(`${interviewPath}$`))
})

// A viewer can't change the interview, so the mark shows them nothing.
test("a viewer isn't shown what to do next", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("whats-next-owner"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const viewer = throwawayEmail("whats-next-viewer")
  const member = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewer, role: "viewer" }
  )
  const page = await signInAs(viewer)
  await api(page, "POST", `/companies/members/invites/${member.token}/accept`)

  await visit(page, `/companies/${company.id}/interviews/${interviewId}?ready=1`)
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(page.getByTestId("whats-next")).toHaveCount(0)
})
