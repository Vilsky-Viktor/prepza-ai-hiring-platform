import { expect, test } from "../fixtures"
import { MIN_QUESTION_SECONDS } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// A candidate given extra time (a disability, say) sees each question's longer time on their
// invite before they start: 100% more doubles it.
test("a candidate given extra time sees the longer time on their invite", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const email = throwawayEmail("extra-time")
  const invite = await api<{ id: string }>(owner, "POST", `/companies/interviews/${interviewId}/candidates`, {
    email,
  })
  await api(owner, "PUT", `/companies/interviews/${interviewId}/candidates/${invite.id}/extra-time`, {
    extra_time: 100,
  })

  const candidate = await signInAs(email)
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  // The seconds per question: the first of the time facts above the start (the whole
  // interview's minutes come after it; the rules are a list).
  const seconds = candidate.getByRole("main").locator("p span.tabular-nums").first()
  await expect(seconds).toHaveText(String(MIN_QUESTION_SECONDS * 2))
  await expect(candidate.getByRole("main").getByRole("button")).toBeVisible()
  await shot(candidate, "extra-time")
})
