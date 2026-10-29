import { expect, test } from "../fixtures"
import { API_URL } from "../constants"
import { api, createCompany, createInterview } from "../helpers/api"
import { inviteToken } from "../helpers/db"
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
  const { key } = await api<{ key: string }>(
    owner,
    "POST",
    `/v1/manage/keys?company_id=${company.id}`,
    { name: "Careers site", expiry: "1", permissions: ["candidates:invite"] }
  )
  const headers = { Authorization: `Bearer ${key}` }
  const path = `${API_URL}/v1/interviews/${interviewId}/candidates`
  const email = throwawayEmail("returning")

  // http off localhost: refused, and no one invited.
  const refused = await owner.request.post(path, {
    headers,
    data: { email, return_url: "http://jobs.acme-e2e.com/done", sign_in: false },
  })
  expect(refused.status()).toBe(422)
  expect((await refused.json()).code).toBe("return_url_invalid")

  // Any https address, with no allowed domains at all: those are only for embedding.
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
  await candidate.getByTestId("start-pledge").filter({ visible: true }).click()
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
