import { type Page } from "@playwright/test"

import { API_URL, HUMAN_CHECK_TOKEN } from "../constants"
import { expect, test } from "../fixtures"
import { api } from "../helpers/api"
import { box, PHONE } from "../helpers/layout"
import { hoverFor, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { tokenOf } from "../helpers/sign-in"
import { throwawayEmail } from "../helpers/users"

type Listed = { id: string; slug: string | null; topic_count: number }
type Step = {
  session: { id: string }
  question: { question_id: string; multi: boolean } | null
  done: boolean
}

// The first page of the practice list, as an English visitor sees it.
const LISTED = "/library/templates?language=en&limit=20"

/** Starts a practice round on the template; its first section, or null when it has no practice
 * questions. */
async function start(user: Page, templateId: string) {
  const response = await user.request.fetch(`${API_URL}/rounds/practice/${templateId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${await tokenOf(user)}`,
      "X-Human-Check": HUMAN_CHECK_TOKEN,
    },
  })

  return response.ok() ? ((await response.json()) as { session_id: string }).session_id : null
}

/** Answers the round's questions in order, as the app's player does, until `topics` sections are
 * answered to the end, or `questions` questions are. */
async function answer(user: Page, sessionId: string, topics: number, questions = Infinity) {
  let step = await api<Step>(user, "POST", `/rounds/sessions/${sessionId}/step`)
  const finished = new Set<string>()
  let answered = 0

  while (step.question && finished.size < topics && answered < questions) {
    answered += 1
    const current = step.session.id
    const pick = step.question.multi ? { picks: [0] } : { option_index: 0 }
    await api(user, "POST", `/rounds/sessions/${current}/answers`, {
      question_id: step.question.question_id,
      ...pick,
    })
    step = await api<Step>(user, "POST", `/rounds/sessions/${current}/step`)

    if (step.session.id !== current || step.done) {
      finished.add(current)
    }
  }
}

/** The status icon after the title in the list's row for the template. */
function statusOf(user: Page, template: Listed) {
  return user
    .getByRole("main")
    .locator(`a[href$="/practice/${template.slug ?? template.id}"]`)
    .locator("[data-status]")
}

// The practice list marks what the talent did on each test: a check while in progress, a double
// check once every topic is answered, nothing before the first answer.
test("the practice list shows the talent's progress on each test", async ({ signInAs }) => {
  const user = await signInAs(throwawayEmail("practice-status"))
  const listed = await api<Listed[]>(user, "GET", LISTED)
  const used: string[] = []

  /** The first template of `candidates` not used yet that has practice questions, started. */
  async function round(candidates: Listed[]) {
    for (const template of candidates.filter((item) => !used.includes(item.id))) {
      const sessionId = await start(user, template.id)

      if (sessionId) {
        used.push(template.id)

        return { template, sessionId }
      }
    }

    throw new Error("Not enough practice tests in the local library")
  }

  const roomy = listed.filter((template) => template.topic_count >= 3)
  // Two topics answered to the end.
  const longer = await round(roomy)
  await answer(user, longer.sessionId, 2)
  // One question answered and the round ended there: still in progress, no topic done.
  const barely = await round(roomy)
  await answer(user, barely.sessionId, 1, 1)
  await api(user, "POST", `/rounds/sessions/${barely.sessionId}/finish-interview`)
  // Every question answered.
  const whole = await round(listed.filter((template) => template.topic_count === 2))
  await answer(user, whole.sessionId, Infinity)
  // Started, nothing answered: not started.
  const opened = await round(listed)

  await visit(user, "/practice")
  await expect(statusOf(user, longer.template)).toHaveAttribute("data-status", "in_progress")
  // Its name carries the topics done of all, the counts the API gave.
  await expect(statusOf(user, longer.template)).toHaveAccessibleName(
    new RegExp(`\\b2/${longer.template.topic_count}\\b`)
  )
  await expect(statusOf(user, barely.template)).toHaveAttribute("data-status", "in_progress")
  await expect(statusOf(user, barely.template)).toHaveAccessibleName(
    new RegExp(`\\b0/${barely.template.topic_count}\\b`)
  )
  await expect(statusOf(user, whole.template)).toHaveAttribute("data-status", "completed")
  await expect(statusOf(user, whole.template)).toHaveAccessibleName(/\b2\/2\b/)
  await expect(statusOf(user, opened.template)).toHaveCount(0)
  await expect(user.getByRole("main").locator("[data-status]")).toHaveCount(3)

  // Hovered, the icon names its state in a tooltip.
  const counts = new RegExp(`\\b2/${longer.template.topic_count}\\b`)
  // The icon's own name is no text, so the only text with its counts is the tooltip.
  await hoverFor(user, statusOf(user, longer.template), user.getByText(counts))
  await shot(user, "tooltip", false)

  for (const scheme of ["light", "dark"] as const) {
    await user.emulateMedia({ colorScheme: scheme })
    await user.setViewportSize({ width: 1280, height: 900 })
    await visit(user, "/practice")
    await expect(statusOf(user, whole.template)).toBeVisible()
    await shot(user, `desktop-${scheme}`, false)
    await user.setViewportSize(PHONE)
    await visit(user, "/practice")
    await expect(statusOf(user, whole.template)).toBeVisible()
    // The list measures its rows once shown: the second starts below the first.
    const rows = user.getByRole("main").getByRole("link")
    await expect
      .poll(async () => (await box(rows.nth(1))).top >= (await box(rows.nth(0))).bottom)
      .toBe(true)
    await shot(user, `phone-${scheme}`)
  }
})

// Someone who never practiced sees no marks.
test("a talent who never practiced sees no marks on the list", async ({ signInAs }) => {
  const user = await signInAs(throwawayEmail("practice-none"))
  await visit(user, "/practice")
  await expect(user.getByRole("main").getByRole("link").first()).toBeVisible()
  await expect(user.getByRole("main").locator("[data-status]")).toHaveCount(0)
})
