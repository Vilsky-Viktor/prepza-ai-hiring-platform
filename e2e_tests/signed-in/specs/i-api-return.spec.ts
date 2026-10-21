import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { inviteToken, verifyCompany } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

// A candidate a company's own platform sent through the API without a sign-in opens the link,
// takes the interview without signing in to prepza, and goes back to that platform at the end.
test("a candidate invited through the API goes back to the company's platform", async ({
  browser,
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await api(owner, "PUT", `/companies/companies/${company.id}/website`, { website: "acme-e2e.com" })
  const { key } = await api<{ key: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    { name: "Careers site", expiry: "1", permissions: ["candidates:invite"] }
  )
  const headers = { Authorization: `Bearer ${key}` }
  const path = `${API_URL}/v1/interviews/${interviewId}/candidates`
  const email = throwawayEmail("returning")

  // Its website entered, not verified yet: refused, and no one invited.
  const unverified = await owner.request.post(path, {
    headers,
    data: { email, return_url: "https://jobs.acme-e2e.com/done", sign_in: false },
  })
  expect(unverified.status()).toBe(422)
  await verifyCompany(company.id, "acme-e2e.com")

  // Off the company's verified website: refused too.
  const off = await owner.request.post(path, {
    headers,
    data: { email, return_url: "https://elsewhere.com/done", sign_in: false },
  })
  expect(off.status()).toBe(422)

  const invited = await owner.request.post(path, {
    headers,
    data: { email, return_url: "https://jobs.acme-e2e.com/done?step=2", sign_in: false },
  })
  expect(invited.status()).toBe(201)
  const candidateId = (await invited.json()).id

  // Not signed in: the link is enough.
  const context = await browser.newContext()
  const candidate = await context.newPage()
  await visit(candidate, `/invite/${await inviteToken(email)}`)
  // The company only: no prepza header or footer.
  await expect(candidate.locator("header, footer")).toHaveCount(0)
  // Its one button starts the interview, with no sign-in asked for.
  await expect(candidate.getByText(company.name).first()).toBeVisible()
  await shot(candidate, "invitation")
  await candidate.getByTestId("start-pledge").click()
  await candidate.getByRole("main").getByRole("button").click()
  await expect(candidate).toHaveURL(/\/sessions\//)
  await expect(candidate.getByRole("dialog")).toHaveCount(0)
  await candidate.getByTestId("finish-interview").click()
  await candidate.getByRole("dialog").getByRole("button").last().click()

  // Finished: the one way on is back to the company's platform, naming the company.
  const back = candidate.getByRole("main").locator("a")
  await expect(back).toHaveAttribute(
    "href",
    `https://jobs.acme-e2e.com/done?step=2&prepza_invite=${candidateId}`
  )
  await expect(back).toContainText(company.name)
  await expect(candidate.locator("header, footer")).toHaveCount(0)
  await shot(candidate, "finished")
  await candidate.setViewportSize({ width: 390, height: 844 })
  await shot(candidate, "finished-phone")
  await context.close()
})
