import { expect, test } from "../fixtures"
import { API_URL, MIN_QUESTION_SECONDS } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { tokenOf } from "../helpers/sign-in"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// A candidate's invite before they start. Given extra time (a disability, say), they see each
// question's longer time on it: 100% more doubles it. They start only after pledging to answer
// on their own, without AI tools or other people: the box gates the start, from the keyboard
// too, the API refuses a start without it, and the candidate's page tells the company they
// pledged.
test("a candidate sees their extra time and pledges to answer on their own before starting", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("pledge")
  const invite = await api<{ id: string }>(
    owner,
    "POST",
    `/companies/interviews/${interviewId}/candidates`,
    { email }
  )
  await api(owner, "PUT", `/companies/interviews/${interviewId}/candidates/${invite.id}/extra-time`, {
    extra_time: 100,
  })
  const token = await inviteToken(email)
  const candidate = await signInAs(email)

  // Not started yet: the company's page doesn't say they pledged.
  const report = `/companies/${company.id}/interviews/${interviewId}/candidates/${invite.id}`
  await visit(owner, report)
  await expect(owner.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(owner.getByTestId("pledged")).toHaveCount(0)

  await visit(candidate, `/invite/${token}`)
  // The seconds per question: the first of the time facts above the start (the whole
  // interview's minutes come after it; the rules are a list).
  const seconds = candidate.getByRole("main").locator("p span.tabular-nums").first()
  await expect(seconds).toHaveText(String(MIN_QUESTION_SECONDS * 2))
  const start = candidate.getByRole("main").getByRole("button")
  const pledge = candidate.getByRole("checkbox")
  await expect(pledge).not.toBeChecked()
  await expect(start).toBeDisabled()
  await shot(candidate, "unchecked")

  // Clicking the line ticks it; again unticks it.
  await candidate.getByTestId("start-pledge").filter({ visible: true }).locator("..").click()
  await expect(pledge).toBeChecked()
  await expect(start).toBeEnabled()
  await pledge.click()
  await expect(start).toBeDisabled()

  // From the keyboard.
  await pledge.focus()
  await candidate.keyboard.press("Space")
  await expect(pledge).toBeChecked()
  await expect(start).toBeEnabled()
  await candidate.setViewportSize(PHONE)
  await shot(candidate, "checked-phone")

  // Any other client is held to it: the API refuses a start without the pledge, with its reason.
  const refused = await candidate.request.fetch(`${API_URL}/companies/invites/${token}/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await tokenOf(candidate)}` },
    data: { pledged: false },
  })
  expect(refused.status()).toBe(422)
  expect((await refused.json()).detail).toBe(
    "Confirm you'll answer on your own, without AI tools or other people, to start."
  )

  await start.click()
  await expect(candidate).toHaveURL(/\/sessions\//)

  // Back on the invite: continuing needs no second pledge.
  await visit(candidate, `/invite/${token}`)
  await expect(start).toBeEnabled()
  await expect(candidate.getByRole("checkbox")).toHaveCount(0)

  await visit(owner, report)
  // The visible one: the page can hold a hidden copy of its part while it streams in.
  await expect(owner.getByTestId("pledged").filter({ visible: true })).toBeVisible()
  await shot(owner, "report")
})
