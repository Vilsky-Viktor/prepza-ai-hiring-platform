import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, createInterview, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { shapeAnswers } from "../helpers/db-rounds"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, throwawayEmail } from "../helpers/users"

type Step = { session: { id: string }; question: { question_id: string } | null }

/** A candidate of a new interview who answered every question and finished, with their answers
 * reshaped (shapeAnswers); the owner's page, the candidate's page path and the questions they
 * got right. */
async function finishedCandidate(
  signInAs: (email: string) => Promise<Page>,
  relayed: boolean,
) {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id, 60)
  const email = throwawayEmail("patterns")
  await inviteCandidate(owner, interviewId, email)
  const candidate = await signInAs(email)
  const { sessions } = await api<{ sessions: { id: string }[] }>(
    candidate,
    "POST",
    `/companies/invites/${await inviteToken(email)}/start`,
    { pledged: true },
  )

  for (const section of sessions) {
    for (;;) {
      const step = await api<Step>(candidate, "POST", `/rounds/sessions/${section.id}/step`)

      if (!step.question) {
        break
      }

      await api(candidate, "POST", `/rounds/sessions/${step.session.id}/answers`, {
        question_id: step.question.question_id,
        option_index: 0,
      })
    }
  }

  await api(candidate, "POST", `/rounds/sessions/${sessions[0].id}/finish-interview`)
  const [row] = await api<{ id: string }[]>(
    owner,
    "GET",
    `/companies/interviews/${interviewId}/candidates`,
  )
  const right = await shapeAnswers(row.id, relayed)

  return {
    owner,
    path: `/companies/${company.id}/interviews/${interviewId}/candidates/${row.id}`,
    scorecard: `/companies/interviews/${interviewId}/candidates/${row.id}`,
    right,
  }
}

// Every finished candidate's page suggests questions they got right to ask about in a live
// interview; with no signal, nothing else.
test("a finished candidate comes with questions to ask about", async ({ signInAs }) => {
  test.setTimeout(240_000)
  const { owner, path, scorecard, right } = await finishedCandidate(signInAs, false)
  await visit(owner, path)
  // The visible one: while the page renders again, Next.js can keep a hidden copy of it.
  const card = owner.getByTestId("answer-patterns").filter({ visible: true })
  const followUps = card.getByTestId("follow-up")

  await expect(card).toBeVisible()
  await expect(card.locator("[data-signal]")).toHaveCount(0)
  await expect(followUps.first()).toBeVisible()
  // Each is one the candidate got right, by its question's id.
  const found = await api<{ answer_patterns: { follow_ups: { question_id: string }[] } }>(
    owner,
    "GET",
    scorecard,
  )
  const asked = found.answer_patterns.follow_ups.map((followUp) => followUp.question_id)
  await expect(followUps).toHaveCount(asked.length)
  expect(asked.every((id) => right.includes(id))).toBe(true)
  // No signal: the PDF report has no answer-pattern box.
  await expect(owner.getByTestId("report-answer-patterns")).toHaveCount(0)
  await shot(owner, "answer-patterns-follow-ups")
})

// Answers that look relayed to an AI: the signals show on the card and in the PDF report.
test("relayed-looking answers show both signals on the page and in the PDF", async ({
  signInAs,
}) => {
  test.setTimeout(240_000)
  const { owner, path } = await finishedCandidate(signInAs, true)
  await visit(owner, path)
  // The visible one: while the page renders again, Next.js can keep a hidden copy of it.
  const card = owner.getByTestId("answer-patterns").filter({ visible: true })

  await expect(card.locator('[data-signal="timing"]')).toBeVisible()
  await expect(card.locator('[data-signal="person_fit"]')).toBeVisible()
  await expect(card.getByTestId("follow-up").first()).toBeVisible()
  // The PDF report, off screen, lists the same signals and no questions.
  const report = owner.getByTestId("report-answer-patterns").filter({ visible: true })
  await expect(report.locator("[data-signal]")).toHaveCount(2)
  await expect(report.getByTestId("follow-up")).toHaveCount(0)
  await shot(owner, "answer-patterns-signals")
})
