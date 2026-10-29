import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, finishOneAnswer, inviteCandidate } from "../helpers/api"
import { failGeneration, inviteToken } from "../helpers/db"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { supportId, supportLink, supportSearch } from "../helpers/support"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

// Each test opens many support pages, each a server render on a busy local stack.
test.setTimeout(300_000)

// A complaint names a company in whatever way its writer has: the support tab finds it from an
// ID, a link, a candidate's email or the name; something unknown finds nothing.
test("superadmin finds a company from a complaint", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const owner = await signInAs(ownerEmail())
  const name = `E2E Support ${randomId()}`
  const company = await createCompany(owner, name)
  const interviewId = await createInterview(owner, company.id)
  const candidate = `candidate-${randomId()}@example.com`
  await inviteCandidate(owner, interviewId, candidate)

  const superadmin = await signInSuperadmin()
  await visit(superadmin, "/superadmin/support")
  await shot(superadmin, "support")
  const opening = supportLink(superadmin, "companies", company.id)

  // Every way finds the company: its ID, an interview's link (any language), the candidate's
  // email in any case, its name; something unknown finds nothing.
  await supportSearch(superadmin, company.id)
  await expect(opening).toHaveCount(1)
  await supportSearch(superadmin, `http://localhost:8090/de/companies/${company.id}/interviews/${interviewId}`)
  await expect(supportLink(superadmin, "interviews", interviewId)).toHaveCount(1)
  await supportSearch(superadmin, candidate.toUpperCase())
  await expect(supportLink(superadmin, "candidates").filter({ hasText: candidate })).toHaveCount(1)
  await expect(supportLink(superadmin, "candidates").filter({ hasText: name })).toHaveCount(1)
  await shot(superadmin, "support-found")
  await expect(await supportSearch(superadmin, `no-such-${randomId()}`)).toHaveCount(0)
  await supportSearch(superadmin, name)
  await expect(opening).toHaveCount(1)
})

// A company's page: its credit history, held credits and members as sections in the admin zone's
// menu (on a phone in the bar under the tabs), and its credits adjusted with a reason the company
// sees, a removal below zero refused. The adjustments' rules are billing's tests
// (test_adjustments.py); the page's data the support routes' (test_superadmin_support.py).
test("superadmin adjusts a company's credits from its page", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  const name = `E2E Support ${randomId()}`
  const company = await createCompany(owner, name)
  const interviewId = await createInterview(owner, company.id)
  const candidate = `candidate-${randomId()}@example.com`
  await inviteCandidate(owner, interviewId, candidate)
  const page = `/superadmin/support/companies/${company.id}`
  const superadmin = await signInSuperadmin()
  await visit(superadmin, page)

  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(name)
  // The history: the welcome credits; held: the invited candidate; members: the owner.
  await expect(superadmin.getByRole("main").getByText("+1,500")).toBeVisible()
  await shot(superadmin, "company")
  // The company's sections are pages under Support in the admin zone's menu: credits at the
  // company's own address, the open one marked.
  const menu = superadmin.getByRole("main").getByRole("navigation")
  const marked = menu.locator('a[aria-current="page"]:visible')
  await expect(marked).toHaveAttribute("href", page)
  await menu.locator(`a[href="${page}?page=reserved"]:visible`).click()
  await expect(superadmin).toHaveURL(new RegExp(`${page}\\?page=reserved$`), { timeout: 90_000 })
  await expect(marked).toHaveAttribute("href", `${page}?page=reserved`)
  await expect(superadmin.getByText(candidate)).toBeVisible()
  // The old tabs' addresses open the matching page.
  await visit(superadmin, `${page}?tab=members`)
  await expect(superadmin).toHaveURL(new RegExp(`${page}\\?page=members$`))
  await expect(superadmin.getByText(ownerAddress)).toBeVisible()

  // On a phone, the sections are in the bar under the tabs, the open one checked.
  await superadmin.setViewportSize({ width: 390, height: 844 })
  const bar = menu.last().getByRole("button")
  await bar.click()
  const sections = superadmin.getByRole("menu").getByRole("menuitem")
  await expect(sections).toHaveCount(5)
  await expect(superadmin.getByRole("menu").locator('[aria-current="page"]')).toHaveAttribute(
    "href",
    `${page}?page=members`
  )
  await shot(superadmin, "company-phone")
  await superadmin.getByRole("menu").locator(`a[href="${page}?page=audit"]`).click()
  await expect(superadmin).toHaveURL(new RegExp(`${page}\\?page=audit$`), { timeout: 90_000 })
  await superadmin.setViewportSize({ width: 1280, height: 800 })
  await visit(superadmin, page)

  // Credits added for a complaint: the history shows the reason, to the company too.
  const note = `Charged twice ${randomId()}`
  await openDialog(superadmin, superadmin.getByTestId("adjust-credits"))
  const dialog = superadmin.getByRole("dialog")
  await dialog.getByRole("spinbutton").fill("500")
  await dialog.getByRole("textbox").fill(note)
  await shot(superadmin, "adjust")
  await dialog.getByRole("button").last().click()
  // The confirmation step, without the fields.
  await expect(dialog.getByRole("spinbutton")).toHaveCount(0)
  await shot(superadmin, "adjust-confirm")
  await dialog.getByRole("button").last().click()
  await expect(superadmin.getByText(note)).toBeVisible()
  await expect(superadmin.getByRole("main").getByText("+500")).toBeVisible()
  await shot(superadmin, "adjusted")

  await visit(owner, `/companies/${company.id}/billing`)
  await expect(owner.getByText(note)).toBeVisible()
  await shot(owner, "owner-history")

  // Removing more than is available is refused, saying why: the history doesn't get it.
  const tooMuch = `Too much ${randomId()}`
  await openDialog(superadmin, superadmin.getByTestId("adjust-credits"))
  await dialog.getByRole("spinbutton").fill("-1000000")
  await dialog.getByRole("textbox").fill(tooMuch)
  await dialog.getByRole("button").last().click()
  await expect(dialog.getByRole("spinbutton")).toHaveCount(0)
  await dialog.getByRole("button").last().click()
  await expect(superadmin.locator('[data-sonner-toast][data-type="error"]')).toContainText(
    "That would take the available balance below zero."
  )
  await expect(dialog).toBeVisible()
  await visit(superadmin, page)
  await expect(superadmin.getByText(note)).toBeVisible()
  await expect(superadmin.getByText(tooMuch)).toHaveCount(0)
})

// From a company's page to its interviews and their candidates: each page says what happened,
// from the data, and links to the next.
test("superadmin follows a company to its interviews and their candidates", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const failedId = await createInterview(owner, company.id)
  await failGeneration(failedId, company.id)
  const candidates = `/companies/interviews/${interviewId}/candidates`
  // One candidate finished (and the owner looked at their results: the audit log has it); one
  // only invited, with extra time.
  const finished = throwawayEmail("finished")
  const done = await api<{ id: string }>(owner, "POST", candidates, { email: finished })
  await finishOneAnswer(await signInAs(finished), finished)
  await api(owner, "GET", `${candidates}/${done.id}`)
  const waiting = throwawayEmail("waiting")
  const invited = await api<{ id: string }>(owner, "POST", candidates, { email: waiting })
  await api(owner, "PUT", `${candidates}/${invited.id}/extra-time`, { extra_time: 50 })
  const topics = (await api<{ topics: { title: string }[] }>(owner, "GET", `/companies/interviews/${interviewId}`))
    .topics

  const superadmin = await signInSuperadmin()
  const page = `/superadmin/support/companies/${company.id}`

  // Its interviews, each opening its page; the audit log: what the owner did, and who.
  await visit(superadmin, `${page}?page=interviews`)
  await expect(supportLink(superadmin, "interviews", interviewId)).toBeVisible()
  await expect(supportLink(superadmin, "interviews", failedId)).toBeVisible()
  await shot(superadmin, "company-interviews")
  await visit(superadmin, `${page}?page=audit`)
  await expect(superadmin.getByRole("main").getByText(ownerAddress).first()).toBeVisible()
  await expect(superadmin.getByRole("main").getByText(finished).first()).toBeVisible()
  await shot(superadmin, "company-audit")

  // A failed generation shows as such, instead of the status.
  await visit(superadmin, `/superadmin/support/interviews/${failedId}`)
  await expect(superadmin.getByRole("main").locator('[data-variant="destructive"]')).toBeVisible()
  await visit(superadmin, `/superadmin/support/interviews/${interviewId}`)
  await expect(superadmin.getByRole("main").locator('[data-variant="destructive"]')).toHaveCount(0)
  await expect(supportLink(superadmin, "companies", company.id)).toBeVisible()

  for (const topic of topics) {
    await expect(superadmin.getByRole("main").getByText(topic.title, { exact: true })).toBeVisible()
  }

  // Its candidates, each opening their page; only the finished one has a grade.
  await expect(supportLink(superadmin, "candidates")).toHaveCount(2)
  await expect(supportLink(superadmin, "candidates", done.id)).toContainText(finished)
  await expect(supportLink(superadmin, "candidates", done.id)).toContainText(/\d+%/)
  await expect(supportLink(superadmin, "candidates", invited.id)).not.toContainText(/\d+%/)
  await shot(superadmin, "interview")

  // The finished candidate: started and finished dates besides the invite's, a grade; the
  // waiting one: their extra time. Each links to the company and the interview.
  const times = superadmin.getByRole("main").locator("dl time")
  const values = superadmin.getByRole("main").locator("dl dd")
  await supportLink(superadmin, "candidates", invited.id).click()
  // The old page stays until the new one arrives, and the dev server may first compile it: wait
  // for the candidate's address before reading the heading.
  await expect(superadmin).toHaveURL(new RegExp(`/superadmin/support/candidates/${invited.id}$`), {
    timeout: 90_000,
  })
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(waiting)
  await expect(supportLink(superadmin, "companies", company.id)).toBeVisible()
  await expect(supportLink(superadmin, "interviews", interviewId)).toBeVisible()
  await expect(values.filter({ hasText: /^\+50%$/ })).toHaveCount(1)
  const waitingTimes = await times.count()
  await shot(superadmin, "candidate-waiting")
  await visit(superadmin, `/superadmin/support/candidates/${done.id}`)
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(finished)
  await expect(times).toHaveCount(waitingTimes + 2)
  await expect(values.filter({ hasText: /\d+%/ })).toHaveCount(1)
  await expect(values.filter({ hasText: /^\+\d+%$/ })).toHaveCount(0)
  await shot(superadmin, "candidate-finished")
})

// An owner's account: their address in another case finds it first, and so does its ID; its page
// lists their companies, each opening its page.
test("superadmin finds an account by its email and its ID", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const superadmin = await signInSuperadmin()
  const found = await supportSearch(superadmin, ownerAddress.toUpperCase())
  await expect(found.first()).toHaveAttribute("href", /\/superadmin\/support\/users\/[^/]+$/)
  await expect(supportLink(superadmin, "companies", company.id)).toHaveCount(1)
  const userId = await supportId(found.first())
  await expect((await supportSearch(superadmin, userId)).first()).toHaveAttribute(
    "href",
    `/superadmin/support/users/${userId}`
  )
  await visit(superadmin, `/superadmin/support/users/${userId}`)
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(ownerAddress)
  await expect(supportLink(superadmin, "companies", company.id)).toBeVisible()
})

test("superadmin suspends, lifts, renames and deletes a company from its page", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const owner = await signInAs(ownerEmail())
  const name = `E2E Moderated ${randomId()}`
  const company = await createCompany(owner, name)
  const interviewId = await createInterview(owner, company.id)
  const candidate = `candidate-${randomId()}@example.com`
  await inviteCandidate(owner, interviewId, candidate)
  const invitePath = `/invite/${await inviteToken(candidate)}`

  const superadmin = await signInSuperadmin()
  // The old companies tab's address leads to support.
  await visit(superadmin, "/superadmin/companies")
  await expect(superadmin).toHaveURL(/\/superadmin\/support$/)
  await visit(superadmin, `/superadmin/support/companies/${company.id}`)

  await superadmin.getByTestId("suspend").click()
  await superadmin.getByRole("dialog").getByRole("button").last().click()
  await expect(superadmin.getByTestId("unsuspend")).toBeVisible()
  await shot(superadmin, "suspended")

  // What a suspended company's members and candidates see (its rules are the companies
  // service's tests).
  await visit(owner, invitePath)
  await shot(owner, "invite-suspended")

  // Clicked again if the first click came while the page was still refreshing.
  await expect(async () => {
    await superadmin.getByTestId("unsuspend").click({ timeout: 5_000 })
    await expect(superadmin.getByTestId("suspend")).toBeVisible({ timeout: 5_000 })
  }).toPass({ timeout: 60_000 })

  // The icons beside Suspend: rename, then delete; beside the visible one, as while the page
  // renders again Next.js can keep a hidden copy of it.
  const actions = superadmin
    .getByTestId("suspend")
    .filter({ visible: true })
    .locator("xpath=following-sibling::span[1]")
    .getByRole("button")

  await actions.first().click()
  await superadmin.getByRole("dialog").getByRole("textbox").fill(`${name} renamed`)
  await superadmin.getByRole("dialog").getByRole("button").last().click()
  await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(`${name} renamed`)

  await actions.last().click()
  await superadmin.getByRole("dialog").getByRole("button").last().click()
  await expect(superadmin).toHaveURL(/\/superadmin\/support$/)
  await expect(await supportSearch(superadmin, company.id)).toHaveCount(0)
})
