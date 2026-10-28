import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, deleteOwnCompanies } from "../helpers/api"
import { box } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { throwawayEmail } from "../helpers/users"

type Detail = { topics: { id: string; question_limit: number }[] }

const SECONDS = 45
// The start button's height: the big size of the start pages.
const START_HEIGHT = 56

// The start page on a computer: the whole interview's minutes beside the time per question, the
// big start button, and the rules card from the screen's top to its bottom, also on a short
// screen, where the rules scroll inside it.
test("the start page shows the whole interview and runs its rules down the screen", async ({
  signInAs,
}) => {
  test.setTimeout(300_000)
  const user = await signInAs(throwawayEmail("start-page"))
  const company = await createCompany(user)
  const interview = await createInterview(user, company.id)

  try {
    // One question from the first topic, at 45 seconds a question.
    const before = await api<Detail>(user, "GET", `/companies/interviews/${interview}`)
    await api(user, "PUT", `/companies/interviews/${interview}/topics/${before.topics[0].id}/limit`, {
      limit: 1,
    })
    await api(user, "PATCH", `/companies/interviews/${interview}/settings`, {
      question_seconds: SECONDS,
    })
    const { topics } = await api<Detail>(user, "GET", `/companies/interviews/${interview}`)
    const questions = topics.reduce((sum, topic) => sum + topic.question_limit, 0)
    const minutes = Math.ceil((questions * SECONDS) / 60)

    for (const size of [
      { width: 1280, height: 800 },
      { width: 1280, height: 480 },
    ]) {
      await user.setViewportSize(size)
      await visit(user, `/companies/${company.id}/interviews/${interview}/try`)
      const start = user.getByTestId("accept-start")
      await expect(start).toBeVisible()

      await expect(user.getByTestId("total-minutes")).toContainText(String(minutes))
      expect((await box(start)).height).toBe(START_HEIGHT)

      const rules = await box(user.getByTestId("invite-rules"))
      expect(rules.top).toBeLessThanOrEqual(1)
      expect(Math.abs(rules.height - size.height)).toBeLessThanOrEqual(1)

      // The way back stays on the screen, beside the test rather than above the rules.
      const back = await box(user.getByTestId("back-link").getByRole("link"))
      expect(back.left).toBeGreaterThanOrEqual(0)
      expect(back.right).toBeLessThanOrEqual(rules.left)
    }

    // On the short screen the rules don't fit: they scroll inside the card.
    const scrolls = await user
      .getByTestId("invite-rules")
      .evaluate((card) => card.scrollHeight > card.clientHeight)
    expect(scrolls).toBe(true)
  } finally {
    await deleteOwnCompanies(user)
  }
})
