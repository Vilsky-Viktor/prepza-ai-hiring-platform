import { expect, test } from "../fixtures"
import { api, createCompany, templatesBySize } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { randomId, throwawayEmail } from "../helpers/users"

// From free practice to hiring: a practice result offers the same test for the user's own
// candidates, in a company they choose: a new one, their only one, or one of several.
test("a practice result leads to using its test in a company", async ({ signInAs }) => {
  const user = await signInAs(throwawayEmail("practice-hire"))
  // A template companies can use, as in CI's seed; a third of its questions are for practice.
  const [template] = await templatesBySize(user)
  const picker = `/companies/templates/${template.id}`
  const opensTemplate = new RegExp(`/companies/[^/]+/templates/${template.id}$`)

  // The result screen, even before the round is finished, offers the test for hiring.
  const round = await api<{ round_id: string }>(user, "POST", `/rounds/practice/${template.id}`)
  await visit(user, `/practice/rounds/${round.round_id}`)
  const hire = user.locator(`a[href="${picker}"]`)
  await expect(hire).toBeVisible()
  await shot(user, "result-hire")

  // No company yet: the choice is empty, and a new company opens on the test.
  await hire.click()
  await user.waitForURL(new RegExp(`${picker}$`))
  await expect(user.getByTestId("new-company").filter({ visible: true })).toBeVisible()
  await expect(user.getByRole("main").getByRole("listitem")).toHaveCount(0)
  await shot(user, "pick-none")
  await user.getByTestId("new-company").click()
  await user.getByRole("dialog").getByRole("textbox").fill(`E2E ${randomId()}`)
  await user.getByRole("dialog").locator('button[type="submit"]').click()
  await user.waitForURL(opensTemplate)
  await expect(user.getByTestId("use-template").filter({ visible: true })).toBeVisible()

  // One company: straight to the test in it.
  await visit(user, picker)
  await user.waitForURL(opensTemplate)

  // Several: each row opens the test in its company, with nothing to remove here.
  const second = await createCompany(user)
  await visit(user, picker)
  const row = user.getByRole("link", { name: new RegExp(second.name) })
  await expect(row).toHaveAttribute("href", `/companies/${second.id}/templates/${template.id}`)
  await expect(user.getByRole("main").getByRole("listitem").getByRole("button")).toHaveCount(0)
  await shot(user, "pick-several")
})

// A finished practice lists its questions by topic, without numbers.
test("a finished practice lists its questions without numbers", async ({ signInAs }) => {
  const user = await signInAs(throwawayEmail("practice-review"))
  const [template] = await templatesBySize(user)
  const round = await api<{ round_id: string }>(user, "POST", `/rounds/practice/${template.id}`)
  const result = await api<{ topics: { session_id: string }[] }>(
    user,
    "GET",
    `/rounds/practice/rounds/${round.round_id}`
  )

  // Ended as the app's player ends it: every section at once.
  await api(user, "POST", `/rounds/sessions/${result.topics[0].session_id}/finish-interview`)

  await visit(user, `/practice/rounds/${round.round_id}`)
  // Each question with its feedback: the report flag, named for screen readers.
  await expect(user.getByRole("button", { name: "Report question" }).first()).toBeVisible()
  await expect(user.getByText(/^\d+\.$/)).toHaveCount(0)
  await shot(user, "practice-review")
})
