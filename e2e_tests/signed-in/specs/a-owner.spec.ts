import { expect, test } from "../fixtures"
import { addTemplate, deleteTemplate } from "../helpers/db-library"
import { openTab, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

// A company owner: a company, an interview from a template, its questions, a candidate invited.
test("owner creates a company, an interview from a template and invites a candidate", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail())
  // No company yet: the list has no rows.
  await expect(owner.getByTestId("new-company")).toBeVisible()
  await expect(owner.getByRole("main").getByRole("listitem")).toHaveCount(0)
  await shot(owner, "companies-empty")

  // The home page's start: the description, then which company. Going on would generate the
  // interview with OpenAI, so the company is created from the companies page instead.
  await visit(owner, "/")
  const start = owner.getByRole("main").locator("form").first()
  await start.getByRole("textbox").fill("Backend developer: SQL basics and indexes.")
  await start.locator('button[type="submit"]').click()
  // No company to pick: only the new company's name to enter.
  await expect(start.locator("textarea")).toHaveCount(0)
  await expect(start.getByRole("radiogroup")).toHaveCount(0)
  await expect(start.getByRole("textbox")).toBeVisible()
  await shot(owner, "home-company-step", false)

  const name = `E2E Owner ${randomId()}`
  await visit(owner, "/companies")
  await owner.getByTestId("new-company").click()
  await owner.getByRole("dialog").getByRole("textbox").fill(name)
  await shot(owner, "new-company-dialog")
  await owner.getByRole("dialog").locator('button[type="submit"]').click()
  await expect(owner).toHaveURL(/\/companies\/[^/]+\/interviews$/)
  const companyUrl = new URL(owner.url()).pathname.replace(/\/interviews$/, "")
  await expect(owner.getByRole("heading", { name })).toBeVisible()
  await expect(owner.getByRole("main").getByRole("listitem")).toHaveCount(0)
  await shot(owner, "interviews-empty")

  // Templates tab: "Use template" on each row. Only templates a company can
  // copy are listed, so using one never fails: a throwaway one with too few questions isn't,
  // though practice lists it; one with enough is, and opens as an interview. They're German, so
  // the lists are asked for German: they start in the visitor's language and English.
  const used = `E2E Copyable ${randomId()}`
  const uncopyable = `E2E Uncopyable ${randomId()}`
  const templateIds = [await addTemplate(used, 10), await addTemplate(uncopyable, 9)]

  try {
    await visit(owner, `/practice?q=${encodeURIComponent(uncopyable)}&lang=de`)
    await expect(owner.getByText(uncopyable)).toBeVisible()
    await visit(owner, `${companyUrl}/templates?q=${encodeURIComponent(uncopyable)}&lang=de`)
    await expect(owner.getByRole("main").getByRole("listitem")).toHaveCount(0)
    await expect(owner.getByText(uncopyable)).toHaveCount(0)

    await visit(owner, `${companyUrl}/interviews`)
    await openTab(owner, "/templates")
    // The filters are lowercase, the level's first among them (language names keep their capitals).
    await expect(owner.getByRole("main").locator("form").getByRole("button").first()).toHaveCSS(
      "text-transform",
      "lowercase"
    )
    await shot(owner, "templates")
    await visit(owner, `${companyUrl}/templates?q=${encodeURIComponent(used)}&lang=de`)
    const row = owner.getByRole("listitem").filter({ hasText: used })
    await row.getByTestId("use-template").click()
    // The local dev server can take a while to build the interview page the first time.
    await expect(owner).toHaveURL(/\/interviews\/[^/?]+$/, { timeout: 90_000 })
  } finally {
    for (const id of templateIds) {
      await deleteTemplate(id)
    }
  }

  await expect(owner.getByTestId("manage-questions").first()).toBeVisible()
  await shot(owner, "interview")

  // The questions of the first topic: the AI warning card and every answer option, each marked
  // right or wrong for screen readers too.
  await owner.getByTestId("manage-questions").first().click()
  const dialog = owner.getByRole("dialog")
  await expect(dialog.getByRole("status")).toBeVisible()
  await expect(dialog.getByRole("img", { name: "Correct answer" }).first()).toBeVisible()
  await expect(dialog.getByRole("img", { name: "Wrong answer" }).first()).toBeVisible()
  // `inline code` in an option shows as code, as in the question, without its backticks.
  await expect(dialog.locator("li code").first()).toHaveText("if is_member:")
  await expect(dialog.getByText("`if is_member:`")).toHaveCount(0)
  await shot(owner, "manage-questions")
  await owner.keyboard.press("Escape")

  const interviewUrl = owner.url()
  // The back arrow, to the company's interviews.
  await owner.getByRole("main").locator('a[href$="/interviews"]').first().click()
  await expect(owner).toHaveURL(/\/interviews$/)
  await expect(owner.getByText(used).first()).toBeVisible()
  await shot(owner, "interviews-list")

  // Inviting a candidate opens the candidate list with them on it.
  await visit(owner, `${interviewUrl}?tab=candidates`)
  const rows = owner.getByRole("main").locator('a[href*="/candidates/"]')
  await expect(rows).toHaveCount(0)
  await shot(owner, "candidates-empty")
  const candidate = throwawayEmail("candidate")
  // The visible one: while the page renders again, Next.js can keep a hidden copy of it.
  await owner.getByTestId("new-candidate").filter({ visible: true }).click()
  // The first tab invites one candidate by email.
  await owner.getByRole("dialog").getByRole("tab").first().click()
  await owner.getByRole("dialog").locator('input[type="email"]').fill(candidate)
  await shot(owner, "invite-dialog")
  await owner.getByRole("dialog").locator('button[type="submit"]').click()
  await expect(owner.getByRole("dialog")).toHaveCount(0)
  // A success toast, naming the invited email.
  await expect(owner.locator('[data-sonner-toast][data-type="success"]')).toContainText(candidate)
  await expect(owner.getByText(candidate, { exact: true }).first()).toBeVisible()
  await expect(rows).toHaveCount(1)
  await shot(owner, "candidates")
})
