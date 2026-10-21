import { expect, test } from "../fixtures"
import { createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// A candidate whose email isn't confirmed yet (GitHub doesn't confirm it) is told to confirm it,
// not that the invite was sent to another address. The emulator confirms every email, so the
// API's answer is played here; the services' own test checks they give it.
test("a candidate whose email isn't confirmed is told to confirm it", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("unconfirmed")
  await inviteCandidate(owner, interviewId, email)

  const candidate = await signInAs(email)
  const token = await inviteToken(email)
  const refusal = "Confirm your email first: open the link we sent you, then try again."
  await candidate.route(`**/api/companies/invites/${token}/start`, (route) =>
    route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({ detail: refusal }),
    }),
  )

  await visit(candidate, `/invite/${token}`)
  await candidate.getByTestId("start-pledge").click()
  await candidate.getByRole("main").getByRole("button").click()
  await expect(candidate.getByText(refusal)).toBeVisible()
  await expect(candidate.getByText("This invite was sent to a different email address.")).toHaveCount(0)
  await shot(candidate, "confirm-email")
})
