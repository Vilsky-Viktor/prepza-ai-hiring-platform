import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// Text that names nothing to test (a recipe, a story) is refused before anything is generated:
// the page says why, word for word as generation says it, and stays where it is. Generation's
// answer is stubbed in the browser (its check is a model call, measured in evals/).
const NOTHING_TO_TEST =
  "This text doesn't name anything to test. Paste a job description, a role, or the skills to test."

test("text that names nothing to test is refused with the reason", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("nothing-to-test"))
  const company = await createCompany(owner)
  let asked = 0
  await owner.route(`**/api/companies/interviews?company_id=${company.id}`, (route) => {
    if (route.request().method() !== "POST") {
      return route.continue()
    }

    asked += 1

    return route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({ detail: NOTHING_TO_TEST }),
    })
  })

  await visit(owner, `/companies/${company.id}/interviews/new`)
  const box = owner.getByRole("main").getByRole("textbox")
  await box.fill("Banana bread: mash three bananas, stir in flour and sugar, bake for an hour.")
  await box.press("ControlOrMeta+Enter")

  await expect(owner.getByText(NOTHING_TO_TEST)).toBeVisible()
  await expect(owner).toHaveURL(/\/interviews\/new$/)
  // What was pasted stays, so it can be fixed.
  await expect(box).toHaveValue(/Banana bread/)
  expect(asked).toBe(1)
  await shot(owner, "refused")
})
