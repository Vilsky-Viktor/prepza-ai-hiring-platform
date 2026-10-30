import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import {
  deleteTemplate,
  MULTI_QUESTION,
  MULTI_RIGHT,
  MULTI_WRONG,
  multiAnswerTemplate,
} from "../helpers/db-library"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { setScheme } from "../helpers/theme"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

type Step = {
  session: { id: string }
  question: { question_id: string; text: string; options: string[]; multi: boolean } | null
}

/** The page at desktop and phone width, each in a screenshot. */
async function shots(page: Page, name: string) {
  await page.setViewportSize({ width: 1280, height: 900 })
  await shot(page, `${name}-desktop`)
  await page.setViewportSize(PHONE)
  await shot(page, `${name}-phone`)
  await page.setViewportSize({ width: 1280, height: 900 })
}

/** Answers single-answer questions of the session through the API, as the player does, until a
 * multi-answer one waits; that step. */
async function stepToMulti(page: Page, sessionId: string): Promise<Step> {
  for (;;) {
    const step = await api<Step>(page, "POST", `/rounds/sessions/${sessionId}/step`)
    expect(step.question, "the draw holds a multi-answer question").not.toBeNull()

    if (step.question!.multi) {
      return step
    }

    await api(page, "POST", `/rounds/sessions/${step.session.id}/answers`, {
      question_id: step.question!.question_id,
      option_index: 0,
    })
  }
}

/** The answered multi-answer question's row on a scorecard or a practice review, scrolled to.
 * Both are virtual lists: only the rows near the screen are in the page, and once the list has
 * measured them the server's first ones may go, so the page is scrolled until the row shows. */
async function scrolledToMulti(page: Page) {
  const rows = page.getByRole("main").getByRole("listitem")
  const row = rows
    .filter({ has: page.getByTestId("multi-choice") })
    .filter({ has: page.locator('[data-verdict="partlyCorrect"]') })
    .first()
  await expect(rows.first()).toBeVisible()
  await expect(async () => {
    if ((await row.count()) === 0) {
      await page.mouse.move(640, 400)
      await page.mouse.wheel(0, 400)
    }

    await row.scrollIntoViewIfNeeded({ timeout: 1_000 })
  }).toPass({ timeout: 60_000 })

  return row
}

// A select-all-that-apply question: the candidate ticks options with check boxes under a hint, a
// partly right answer earns part of its point, and the scorecard, the practice review and the
// question lists show it.
test("a multi-answer question is ticked, scored in part and shown", async ({ signInAs }) => {
  test.setTimeout(300_000)
  const template = await multiAnswerTemplate(`E2E multi ${randomId()}`)

  try {
    const owner = await signInAs(ownerEmail())
    await setScheme(owner, "dark")
    const company = await createCompany(owner)
    const interview = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template },
    )
    await api(owner, "PATCH", `/companies/interviews/${interview.id}/settings`, {
      question_seconds: 300,
    })

    // The questions list labels the multi-answer ones.
    await visit(owner, `/companies/${company.id}/interviews/${interview.id}`)
    await owner.getByTestId("manage-questions").first().click()
    const dialog = owner.getByRole("dialog")
    const labelled = dialog.getByText(MULTI_QUESTION, { exact: false })
    // Loaded first: the count is read once.
    await expect(labelled.first()).toBeVisible()
    await expect(dialog.getByTestId("multi-choice")).toHaveCount(await labelled.count())
    await expect(dialog.getByTestId("multi-choice").first()).toBeVisible()
    await shots(owner, "question-list")
    await owner.keyboard.press("Escape")

    // The candidate reaches the multi-answer question of their draw.
    const email = throwawayEmail("multi-candidate")
    await inviteCandidate(owner, interview.id, email)
    const candidate = await signInAs(email)
    await setScheme(candidate, "dark")
    const { sessions } = await api<{ sessions: { id: string }[] }>(
      candidate,
      "POST",
      `/companies/invites/${await inviteToken(email)}/start`,
      { pledged: true },
    )
    const main = candidate.getByRole("main")

    // A single-answer question: no tag, hint or check boxes.
    async function singleShown() {
      await expect(main.getByRole("button", { pressed: false }).first()).toBeVisible()
      await expect(candidate.getByTestId("multi-choice")).toHaveCount(0)
      await expect(candidate.getByTestId("select-all")).toHaveCount(0)
      await expect(candidate.getByTestId("option-check")).toHaveCount(0)
      await shots(candidate, "question-single")
    }

    // The draw holds one multi-answer question; the first one shown is single-answer, unless
    // that one comes first, when the next one is.
    const first = await api<Step>(candidate, "POST", `/rounds/sessions/${sessions[0].id}/step`)
    await visit(candidate, `/sessions/${first.session.id}`)

    if (!first.question!.multi) {
      await singleShown()
    }

    const step = await stepToMulti(candidate, sessions[0].id)
    await visit(candidate, `/sessions/${step.session.id}`)
    await expect(main.getByText(step.question!.text.split("(")[0].trim())).toBeVisible()
    await expect(candidate.getByTestId("multi-choice").filter({ visible: true })).toBeVisible()
    await expect(candidate.getByTestId("select-all").filter({ visible: true })).toBeVisible()
    await expect(candidate.getByTestId("option-check")).toHaveCount(4)
    await shots(candidate, "question-multi")

    // Two right options ticked, each on its own: both stay picked.
    const option = (text: string) =>
      main.getByRole("button", { name: new RegExp(`^[A-D]\\s*${text}$`) })
    await option(MULTI_RIGHT[0]).click()
    await option(MULTI_RIGHT[1]).click()
    await expect(option(MULTI_RIGHT[0])).toHaveAttribute("aria-pressed", "true")
    await expect(option(MULTI_RIGHT[1])).toHaveAttribute("aria-pressed", "true")
    await expect(option(MULTI_WRONG)).toHaveAttribute("aria-pressed", "false")
    await shots(candidate, "question-multi-picked")
    await candidate.getByTestId("next-question").click()
    // Saved, and the next question (or the end of the section) is on screen.
    await expect(candidate.getByTestId("select-all")).toHaveCount(0)

    if (first.question!.multi) {
      await singleShown()
    }

    await api(candidate, "POST", `/rounds/sessions/${sessions[0].id}/finish-interview`)

    // The scorecard: the ticks, each marked right or wrong, and two thirds of the point.
    const [row] = await api<{ id: string }[]>(
      owner,
      "GET",
      `/companies/interviews/${interview.id}/candidates`,
    )
    await visit(owner, `/companies/${company.id}/interviews/${interview.id}/candidates/${row.id}`)
    // The ticked multi-answer question, tagged, is partly correct with two thirds of the point.
    const drawnMulti = await scrolledToMulti(owner)
    await expect(drawnMulti).toContainText(MULTI_QUESTION)
    await expect(drawnMulti.getByTestId("answer-points")).toContainText("0.67")
    await shots(owner, "scorecard")

    // Practice: the same partial point in the review, with every right option shown.
    const learner = await signInAs(throwawayEmail("multi-practice"))
    await setScheme(learner, "dark")
    const round = await api<{ round_id: string }>(learner, "POST", `/rounds/practice/${template}`)
    const result = await api<{ topics: { session_id: string }[] }>(
      learner,
      "GET",
      `/rounds/practice/rounds/${round.round_id}`,
    )
    const practiceStep = await stepToMulti(learner, result.topics[0].session_id)
    const picks = MULTI_RIGHT.slice(0, 2).map((text) =>
      practiceStep.question!.options.indexOf(text),
    )
    await api(learner, "POST", `/rounds/sessions/${practiceStep.session.id}/answers`, {
      question_id: practiceStep.question!.question_id,
      picks,
    })
    await api(learner, "POST", `/rounds/sessions/${practiceStep.session.id}/finish-interview`)
    await visit(learner, `/practice/rounds/${round.round_id}`)
    const practiceMulti = await scrolledToMulti(learner)
    await expect(practiceMulti).toContainText(MULTI_QUESTION)
    await expect(practiceMulti.getByTestId("answer-points")).toContainText("0.67")
    await shots(learner, "practice-review")
  } finally {
    await deleteTemplate(template)
  }
})
