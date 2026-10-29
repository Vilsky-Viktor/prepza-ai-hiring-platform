import type { Page, Response } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { addTemplate, deleteTemplate, lengthenQuestions } from "../helpers/db-library"
import { box, PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"

// A long tail for every question, so it runs taller than the screen leaves for it.
const LONG = "The members list is read again after each change before the next step runs. "
  .repeat(40)
  .trim()

/** A candidate's first question of an interview made from `template`, on screen. */
async function openQuestion(
  owner: Page,
  template: string,
  signInAs: (email: string) => Promise<Page>,
) {
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
  const email = throwawayEmail("layout-candidate")
  await inviteCandidate(owner, interview.id, email)
  const candidate = await signInAs(email)
  const { sessions } = await api<{ sessions: { id: string }[] }>(
    candidate,
    "POST",
    `/companies/invites/${await inviteToken(email)}/start`,
    { pledged: true },
  )
  const step = await api<{ session: { id: string } }>(
    candidate,
    "POST",
    `/rounds/sessions/${sessions[0].id}/step`,
  )
  await candidate.setViewportSize({ width: 1280, height: 900 })
  await visit(candidate, `/sessions/${step.session.id}`)

  return candidate
}

// The question on the start side with its rating under it, the options beside them; on phones
// stacked, the options the screen's width and the rating last. The rating shows before any pick,
// and a question too long for its box scrolls in it, reachable by the keyboard.
test("an interview question sits beside its options and rates before a pick", async ({
  signInAs,
}) => {
  test.setTimeout(240_000)
  const template = await addTemplate(`E2E layout ${randomId()}`, 12)

  try {
    await lengthenQuestions(template, LONG)
    const owner = await signInAs(ownerEmail())
    const candidate = await openQuestion(owner, template, signInAs)
    const main = candidate.getByRole("main")
    const card = candidate.getByTestId("question-card")
    const rating = candidate.getByTestId("question-rating")
    const options = [
      main.getByRole("button", { name: /Check .*first/ }),
      main.getByRole("button", { name: /Skip the check/ }),
    ]
    await expect(card).toContainText(LONG.slice(0, 40))

    // Desktop: the rating shows with nothing picked, under the question, both left of the options.
    await expect(rating).toBeVisible()

    for (const option of options) {
      await expect(option).toHaveAttribute("aria-pressed", "false")
    }

    const desktopCard = await box(card)
    const desktopRating = await box(rating)
    const desktopOption = await box(options[0])
    expect(desktopCard.right).toBeLessThanOrEqual(desktopOption.left)
    expect(desktopRating.right).toBeLessThanOrEqual(desktopOption.left)
    expect(desktopRating.top).toBeGreaterThanOrEqual(desktopCard.bottom)

    // The long question scrolls in its own box, a named region the keyboard can focus and scroll.
    await expect(card).toHaveAttribute("role", "region")
    await expect(card).toHaveAttribute("tabindex", "0")
    await expect(card).toHaveAccessibleName(/.+/)
    await card.focus()
    await expect(card).toBeFocused()
    await candidate.keyboard.press("End")
    await expect.poll(() => card.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
    await shot(candidate, "question-desktop", false)

    // Phone: stacked, the question and the options as wide as the screen, the rating after them.
    await candidate.setViewportSize(PHONE)
    // Nothing to scroll in on a phone: the box grows with the question.
    await expect(card).not.toHaveAttribute("tabindex")
    await expect(card).not.toHaveAttribute("role")
    // The page's width (the scroll bar left out), which the page's main area spans on a phone.
    const { width } = await box(main)
    // The question's gray card, out to the screen's edges.
    const phoneCard = await box(candidate.getByTestId("question-box"))
    expect(phoneCard.left).toBe(0)
    expect(phoneCard.width).toBe(width)
    const phoneOptions = await Promise.all(options.map((option) => box(option)))

    for (const option of phoneOptions) {
      expect(option.left).toBe(0)
      expect(option.width).toBe(width)
      expect(option.top).toBeGreaterThanOrEqual(phoneCard.bottom)
    }

    const lowest = Math.max(...phoneOptions.map((option) => option.bottom))
    expect((await box(rating)).top).toBeGreaterThanOrEqual(lowest)
    await shot(candidate, "question-phone")
  } finally {
    await deleteTemplate(template)
  }
})

// Code for some of the questions, so they take longer to read than the others.
const CODE =
  "What does this print?\n```python\n" +
  Array.from({ length: 12 }, (_, index) => `total = total + item_${index}`).join("\n") +
  "\n```"
const AVERAGE = 60

/** A duration as the report writes it. */
function duration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60

  if (m === 0) {
    return `${s} s`
  }

  return s === 0 ? `${m} min` : `${m} min ${s} s`
}

// Each question has its own time, fitted to its length: the timer counts down that question's
// time, the times differ and add up to the whole interview the invite page shows. A question's
// code sits under its card, and the report shows each answer's time out of the question's.
test("each question has its own time, adding up to the whole interview", async ({
  signInAs,
}) => {
  test.setTimeout(240_000)
  const template = await addTemplate(`E2E times ${randomId()}`, 12)

  try {
    await lengthenQuestions(template, CODE, [0, 2, 4, 6, 8, 10])
    const owner = await signInAs(ownerEmail())
    const company = await createCompany(owner)
    const interview = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template },
    )
    await api(owner, "PATCH", `/companies/interviews/${interview.id}/settings`, {
      question_seconds: AVERAGE,
    })
    const email = throwawayEmail("times-candidate")
    await inviteCandidate(owner, interview.id, email)
    const candidate = await signInAs(email)
    // Each question's own time, as the server sends it with the question.
    const times: number[] = []
    candidate.on("response", async (response: Response) => {
      if (response.request().method() === "POST" && response.url().endsWith("/step")) {
        const step = await response.json()

        if (step.question) {
          times.push(step.question.seconds)
        }
      }
    })
    await visit(candidate, `/invite/${await inviteToken(email)}`)
    const total = candidate.getByTestId("total-minutes").filter({ visible: true })
    await expect(total).toBeVisible()
    const minutes = Number((await total.textContent())?.match(/\d+/)?.[0])
    await candidate.getByTestId("start-pledge").filter({ visible: true }).click()
    await candidate.getByRole("main").getByRole("button").click()
    await expect(candidate).toHaveURL(/\/sessions\//)

    const card = candidate.getByTestId("question-card")
    const questionBox = candidate.getByTestId("question-box")
    const question = questionBox.getByRole("heading")
    const options = candidate.getByRole("main").locator("li > button[aria-pressed]")
    const footer = candidate.locator("[data-round-footer]")
    const { total_questions: count } = await api<{ total_questions: number }>(
      owner,
      "GET",
      `/companies/interviews/${interview.id}`,
    )
    let codeChecked = false

    for (let shown = 1; shown <= count; shown++) {
      await expect.poll(() => times.length).toBe(shown)
      await expect(options.first()).toBeVisible()
      // The timer starts from this question's own time.
      const own = times[shown - 1]
      const [m, s] = ((await candidate.getByRole("timer").textContent()) ?? "").split(":")
      const left = Number(m) * 60 + Number(s)
      expect(left).toBeLessThanOrEqual(own)
      expect(left).toBeGreaterThan(own - 10)

      // Code under the question's card, outside it.
      if (!codeChecked && (await card.locator("pre").count())) {
        await expect(questionBox.locator("pre")).toHaveCount(0)
        expect((await box(card.locator("pre").first())).top).toBeGreaterThanOrEqual(
          (await box(questionBox)).bottom,
        )
        await shot(candidate, "question-code")
        codeChecked = true
      }

      await options.first().click()

      // The last one is answered as the interview finishes.
      if (shown < count) {
        const text = await question.textContent()
        await footer.getByRole("button").last().click()
        await expect(question).not.toHaveText(text ?? "")
      }
    }

    expect(codeChecked).toBe(true)
    // The times differ, and add up to the whole interview shown before the start.
    expect(new Set(times).size).toBeGreaterThan(1)
    expect(times.reduce((sum, time) => sum + time, 0)).toBe(times.length * AVERAGE)
    expect(minutes).toBe(times.length)
    await candidate.getByTestId("finish-interview").click()
    await expect(candidate.getByRole("dialog")).toBeVisible()
    await candidate.getByRole("dialog").getByRole("button").last().click()
    await expect(footer).toHaveCount(0)

    // The report: each answer's time out of its question's own.
    await visit(owner, `/companies/${company.id}/interviews/${interview.id}?tab=candidates`)
    await owner.getByText(email, { exact: true }).first().click()
    // The list renders the answers near the screen only: the first ones, in the order shown.
    const lines = owner.getByTestId("answer-time").filter({ visible: true })

    for (const [index, time] of times.slice(0, 3).entries()) {
      // The question's time ends the line, before any warning of a fast answer.
      await expect(lines.nth(index)).toHaveText(new RegExp(`${duration(time)}(:.*)?$`))
    }

    await shot(owner, "report-limits")
  } finally {
    await deleteTemplate(template)
  }
})
