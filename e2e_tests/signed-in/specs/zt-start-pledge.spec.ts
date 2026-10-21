import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { tokenOf } from "../helpers/sign-in"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// A candidate starts only after pledging to answer on their own, without AI tools or other people:
// the box gates the start, from the keyboard too, the API refuses a start without it, and the
// candidate's page tells the company they pledged.
test("a candidate pledges to answer on their own before starting", async ({ signInAs }) => {
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
  const token = await inviteToken(email)
  const candidate = await signInAs(email)

  // Not started yet: the company's page doesn't say they pledged.
  const report = `/companies/${company.id}/interviews/${interviewId}/candidates/${invite.id}`
  await visit(owner, report)
  await expect(owner.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(owner.getByTestId("pledged")).toHaveCount(0)

  await visit(candidate, `/invite/${token}`)
  const start = candidate.getByRole("main").getByRole("button")
  const pledge = candidate.getByRole("checkbox")
  await expect(pledge).not.toBeChecked()
  await expect(start).toBeDisabled()
  await shot(candidate, "unchecked")

  // Clicking the line ticks it; again unticks it.
  await candidate.getByTestId("start-pledge").locator("..").click()
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
  await expect(owner.getByTestId("pledged")).toBeVisible()
  await shot(owner, "report")
})
