import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { failGeneration } from "../helpers/db"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// An interview whose generation failed says so, in the list and on its page, instead of
// looking like it's still generating.
test("an interview whose generation failed says so", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("generation-failed"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await failGeneration(interviewId, company.id)

  await visit(owner, `/companies/${company.id}/interviews`)
  const row = owner.getByRole("main").getByTestId("generation-failed")
  await expect(row).toHaveAttribute("href", `/companies/${company.id}/interviews/${interviewId}`)
  await shot(owner, "list")

  await visit(owner, `/companies/${company.id}/interviews/${interviewId}`)
  await expect(owner.getByRole("heading", { level: 1 })).toHaveAttribute(
    "data-testid",
    "generation-failed"
  )
  await shot(owner, "page")
})

// Until its first top-up, a company has one generated interview waiting without candidates
// before it generates another: the attempt says how to go on, and nothing is generated.
test("an unpaid company with a generated interview waiting is asked to invite or delete it", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("waiting-limit"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  await failGeneration(interviewId, company.id)

  await visit(owner, `/companies/${company.id}/interviews/new`)
  const description = owner.getByRole("main").getByRole("textbox")
  await description.fill("Senior accountant: month-end close, IFRS reporting and audits.")
  await description.press("ControlOrMeta+Enter")
  await expect(
    owner.getByText(
      "Invite a candidate to one of your interviews, or delete one, before generating another: until your first top-up, your company's limit of generated interviews waiting without candidates is 1."
    )
  ).toBeVisible()
  await expect(owner).toHaveURL(/\/interviews\/new$/)
  await shot(owner, "waiting-limit")
})

// ⌘/Ctrl+Enter pressed twice before the first request finished asks for one interview.
test("a description sent twice quickly asks for one interview", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("double-submit"))
  const company = await createCompany(owner)
  let asked = 0
  // The first request stays unanswered until both presses are in.
  let answer = () => {}
  const answered = new Promise<void>((resolve) => (answer = resolve))
  await owner.route(`**/api/companies/interviews?company_id=${company.id}`, async (route) => {
    if (route.request().method() !== "POST") {
      return route.continue()
    }

    asked += 1
    await answered
    // Refused, so nothing is generated.
    await route.fulfill({
      status: 429,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Too many requests. Try again later." }),
    })
  })

  await visit(owner, `/companies/${company.id}/interviews/new`)
  const box = owner.getByRole("main").getByRole("textbox")
  await box.fill("Senior accountant: month-end close, IFRS reporting and audits.")
  await box.press("ControlOrMeta+Enter")
  await box.press("ControlOrMeta+Enter")
  answer()

  await expect(owner.getByText("Too many requests. Try again later.").filter({ visible: true })).toBeVisible()
  expect(asked).toBe(1)
})
