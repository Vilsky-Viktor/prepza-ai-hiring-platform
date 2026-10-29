import type { Page } from "@playwright/test"

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
    const phoneCard = await box(card)
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
