import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { box } from "../helpers/layout"
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

type Ids = { company: string; interview: string; candidate: string }

/** The owner's throwaway company, with an interview and a candidate invited to it. */
async function companyWithCandidate(owner: Page): Promise<Ids> {
  const company = await createCompany(owner)
  const interview = await createInterview(owner, company.id)
  await inviteCandidate(owner, interview, throwawayEmail("candidate"))
  const [candidate] = await api<{ id: string }[]>(
    owner,
    "GET",
    `/companies/interviews/${interview}/candidates?sort=date&limit=5`
  )

  return { company: company.id, interview, candidate: candidate.id }
}

// Every page from the companies list inward has an info button under its back arrow, opening a
// short guide to that page, each page its own: the guide rounds serves for it, which the
// assistant reads too. One test a page, so they run side by side. Each page, with its guide's
// key and its screenshot's name.
const PAGES: { path: (ids: Ids) => string; key: string; name: string }[] = [
  { path: () => "/top-up", key: "topUp", name: "top-up" },
  { path: () => "/settings", key: "settings", name: "settings" },
  { path: (ids) => `/companies/${ids.company}/members`, key: "team", name: "team" },
  { path: (ids) => `/companies/${ids.company}/interviews/${ids.interview}`, key: "interviewTopics", name: "topics" },
  {
    path: (ids) => `/companies/${ids.company}/interviews/${ids.interview}?tab=candidates`,
    key: "interviewCandidates",
    name: "candidates",
  },
  {
    path: (ids) => `/companies/${ids.company}/interviews/${ids.interview}/candidates/${ids.candidate}`,
    key: "candidate",
    name: "candidate-report",
  },
]

for (const { path, key, name } of PAGES) {
  test(`the info button explains the ${name} page`, async ({ signInAs }) => {
    const owner = await signInAs(ownerEmail())
    await visit(owner, path(await companyWithCandidate(owner)))
    const guide = await api<{ title: string }>(owner, "GET", `/site/help/pages/${key}`)
    expect(await checkHelp(owner, name)).toBe(guide.title)
  })
}

// The companies list: its guide, and the back arrow before it. On a wide screen the arrow sits in
// the page margin before the title, level with it, with a clear gap between the two; at 1280px
// the margin can't hold them, so the arrow and the info button sit on the screen above the title,
// never past its edge, and both work: the arrow goes home.
test("the companies list's info button and back arrow", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  await owner.setViewportSize({ width: 1440, height: 900 })
  await visit(owner, "/companies")
  const back = owner.getByTestId("back-link")
  const arrow = await box(back.getByRole("link"))
  const title = await box(owner.getByRole("main").getByRole("heading", { level: 1 }))
  // Before the title, not touching it, and level with it: its middle within the title's height.
  expect(arrow.right).toBeLessThanOrEqual(title.left - 12)
  const middle = arrow.top + arrow.height / 2
  expect(middle).toBeGreaterThanOrEqual(title.top)
  expect(middle).toBeLessThanOrEqual(title.top + title.height)

  await owner.setViewportSize({ width: 1280, height: 800 })

  for (const control of [back.getByRole("link"), back.getByTestId("page-help")]) {
    const { left, right } = await box(control)
    expect(left).toBeGreaterThanOrEqual(0)
    expect(right).toBeLessThanOrEqual(1280)
  }

  const guide = await api<{ title: string }>(owner, "GET", "/site/help/pages/companies")
  expect(await checkHelp(owner, "companies")).toBe(guide.title)
  await back.getByRole("link").click()
  await expect(owner).toHaveURL(/\/$/)
})

// A page whose guide names a guide article links it: the article rounds names, which opens.
test("the candidate page's guide links its guide article", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const ids = await companyWithCandidate(owner)
  const guide = await api<{ article: { title: string; path: string } }>(
    owner,
    "GET",
    "/site/help/pages/candidate"
  )
  await visit(owner, `/companies/${ids.company}/interviews/${ids.interview}/candidates/${ids.candidate}`)
  await openDialog(owner, owner.getByRole("main").getByTestId("page-help"))
  const link = owner.getByRole("dialog").getByRole("link", { name: guide.article.title })
  await expect(link).toHaveAttribute("href", guide.article.path)
  await link.click()
  await expect(owner).toHaveURL(new RegExp(`${guide.article.path}$`))
  await expect(owner.getByRole("heading", { level: 1 })).toHaveText(guide.article.title)
})
