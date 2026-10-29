import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

type Row = { id: string; tab_leaves: number }

// A page leave counts when it lasted 2 seconds or more: a moment's one (a notification taking
// focus) is kept but not counted.
test("only a real page leave counts", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("signals")
  await inviteCandidate(owner, interviewId, email)

  const candidate = await signInAs(email)
  // The page's clock is Playwright's, so time away passes at once.
  await candidate.clock.install()
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  await candidate.getByTestId("start-pledge").filter({ visible: true }).click()
  await candidate.getByRole("main").getByRole("button").click()
  await expect(candidate).toHaveURL(/\/sessions\//)
  await expect(candidate.getByRole("main").locator("button[aria-pressed]").first()).toBeVisible()

  // Each report is saved before the next is sent: time away passes at once, so without waiting
  // the return could reach the server before the leave it closes.
  const reported = () =>
    candidate.waitForResponse((response) => response.url().endsWith("/signals"))

  async function leave(milliseconds: number) {
    const left = reported()
    await candidate.evaluate(() => window.dispatchEvent(new Event("blur")))
    await left
    await candidate.clock.fastForward(milliseconds)
    const back = reported()
    await candidate.evaluate(() => window.dispatchEvent(new Event("focus")))
    await back
  }

  await leave(300)
  await leave(2_500)

  const leaves = async () => {
    const [row] = await api<Row[]>(owner, "GET", `/companies/interviews/${interviewId}/candidates`)

    return row?.tab_leaves
  }

  await expect.poll(leaves).toBe(1)

  const [row] = await api<Row[]>(owner, "GET", `/companies/interviews/${interviewId}/candidates`)
  await visit(owner, `/companies/${company.id}/interviews/${interviewId}/candidates/${row.id}`)
  // The candidate's results, with the note on their score and signals.
  await expect(owner.getByTestId("human-review").filter({ visible: true })).toBeVisible()
  await shot(owner, "results-note")
})
