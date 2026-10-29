import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

/** Opens the page's info button, checks its dialog has a guide (its lists of what to do and
 * tips), and closes it; returns the guide's title, to tell the pages' guides apart. */
async function checkHelp(page: Page, name: string) {
  await openDialog(page, page.getByRole("main").getByTestId("page-help"))
  const dialog = page.getByRole("dialog")
  await expect(dialog.getByRole("listitem").first()).toBeVisible()
  const title = (await dialog.getByRole("heading").first().textContent()) ?? ""
  await shot(page, name)
  await dialog.getByRole("button").last().click()
  await expect(dialog).toBeHidden()

  return title
}

// Every page from the companies list inward has an info button under its back arrow, opening a
// short guide to that page, each page its own; the companies list's arrow goes home.
test("the info buttons explain the companies list, an interview and a candidate", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await inviteCandidate(owner, interviewId, throwawayEmail("candidate"))
  const [candidate] = await api<{ id: string }[]>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}/candidates?sort=date&limit=5`
  )
  const interviewHref = `/companies/${company.id}/interviews/${interviewId}`
  // Each page, with its guide's key and its screenshot's name.
  const pages = [
    ["/companies", "companies", "companies"],
    [interviewHref, "interviewTopics", "topics"],
    [`${interviewHref}?tab=candidates`, "interviewCandidates", "candidates"],
    [`${interviewHref}/candidates/${candidate.id}`, "candidate", "candidate-report"],
    [`/companies/${company.id}/members`, "team", "team"],
    ["/top-up", "topUp", "top-up"],
    ["/settings", "settings", "settings"],
  ]

  for (const [path, key, name] of pages) {
    await visit(owner, path)
    // The guide rounds serves for the page, which the assistant reads too.
    const guide = await api<{ title: string }>(owner, "GET", `/site/help/pages/${key}`)
    expect(await checkHelp(owner, name)).toBe(guide.title)
  }

  // The companies list's back arrow goes to the home page.
  await visit(owner, "/companies")
  const home = owner.getByRole("main").locator('a[href="/"]')
  await home.click()
  await expect(owner).toHaveURL(/\/$/)
})

// A page whose guide names a guide article links it: the article rounds names, which opens.
test("the candidate page's guide links its guide article", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await inviteCandidate(owner, interviewId, throwawayEmail("candidate"))
  const [candidate] = await api<{ id: string }[]>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}/candidates?sort=date&limit=5`
  )
  const guide = await api<{ article: { title: string; path: string } }>(
    owner,
    "GET",
    "/site/help/pages/candidate"
  )
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}/candidates/${candidate.id}`)
  await openDialog(owner, owner.getByRole("main").getByTestId("page-help"))
  const link = owner.getByRole("dialog").getByRole("link", { name: guide.article.title })
  await expect(link).toHaveAttribute("href", guide.article.path)
  await link.click()
  await expect(owner).toHaveURL(new RegExp(`${guide.article.path}$`))
  await expect(owner.getByRole("heading", { level: 1 })).toHaveText(guide.article.title)
})
