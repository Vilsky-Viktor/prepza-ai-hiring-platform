import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { addTemplate, deleteTemplate } from "../helpers/db-library"
import { openDialog, visit } from "../helpers/navigation"
import { throwawayEmail } from "../helpers/users"

// Text in another language than the page carries its own lang and dir, so screen readers read
// it in that language and a right-to-left one reads right to left (WCAG 3.1.2).

// An interview's topics and questions are in its language (this German template's), whatever
// the interface's.
test("an interview's topics and questions carry the interview's language", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("text-language"))
  const templateId = await addTemplate("E2E text language", 12)

  try {
    const company = await createCompany(owner)
    const interview = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: templateId }
    )
    const detail = await api<{ language: string }>(
      owner,
      "GET",
      `/companies/interviews/${interview.id}`
    )
    expect(detail.language).toBe("de")

    await visit(owner, `/companies/${company.id}/interviews/${interview.id}`)
    const topics = owner.getByRole("main").locator('[lang="de"][dir="ltr"]')
    await expect(topics.getByText("E2E topic")).toBeVisible()

    await openDialog(owner, owner.getByTestId("manage-questions").first())
    const questions = owner.getByRole("dialog").locator('[lang="de"]')
    await expect(questions.getByText("E2E question 1?")).toBeVisible()
  } finally {
    await deleteTemplate(templateId)
  }
})

// A language picker names each language in itself, marked as that language: Japanese's name
// in Japanese, Arabic's right to left.
test("the language picker marks each language's own name with its language", async ({
  signInAs,
}) => {
  const user = await signInAs(throwawayEmail("language-names"))
  await visit(user, "/settings")
  await user.getByRole("main").getByRole("combobox").first().click()
  const options = user.getByRole("option")
  await expect(options.first()).toBeVisible()

  await expect(options.locator('[lang="ja"][dir="ltr"]')).toHaveCount(1)
  await expect(options.locator('[lang="ar"][dir="rtl"]')).toHaveCount(1)
})
