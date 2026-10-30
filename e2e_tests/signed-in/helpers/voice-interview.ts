import { expect, type Page } from "@playwright/test"

import { api, createCompany, inviteCandidate } from "./api"
import { inviteToken } from "./db"
import { deleteTemplate, multiAnswerTemplate } from "./db-library"
import { visit } from "./navigation"
import { ownerEmail, randomId, throwawayEmail } from "./users"
import { fakeMicrophone, fakeMira, noReadingAloud } from "./voice"

// How long the screen may take to start listening.
export const LISTENING_MS = 45_000

type Step = {
  session: { id: string; answered: number; total: number }
  question: { question_id: string; multi: boolean } | null
}

/** Starts the invite's interview and answers its questions by API until the one on screen is
 * `wanted` (multi-answer or not) with a question after it, as the player does: of the draw's 10,
 * 4 are multi-answer and 6 not, so one of each that isn't the last always comes. */
export async function onQuestion(candidate: Page, token: string, multi: boolean) {
  const { sessions } = await api<{ sessions: { id: string }[] }>(
    candidate,
    "POST",
    `/companies/invites/${token}/start`,
    { pledged: true }
  )

  for (;;) {
    const step = await api<Step>(candidate, "POST", `/rounds/sessions/${sessions[0].id}/step`)
    expect(step.question, "the draw holds the question wanted").not.toBeNull()

    if (step.question!.multi === multi && step.session.answered + 1 < step.session.total) {
      return
    }

    await api(candidate, "POST", `/rounds/sessions/${step.session.id}/answers`, {
      question_id: step.question!.question_id,
      option_index: 0,
    })
  }
}

/** Continues the invite's voice interview on screen, the microphone allowed first, until Mira
 * listens. */
export async function continued(candidate: Page, token: string) {
  await visit(candidate, `/invite/${token}`)
  await candidate.getByTestId("voice-access").getByRole("button").click()
  await candidate.getByRole("main").getByRole("button").last().click()
  await expect(candidate).toHaveURL(/\/sessions\//)
  const turn = candidate.getByTestId("voice-turn")
  // Listening starts once the speech detector's WebAssembly is compiled: slow on a busy stack.
  await expect(turn).toHaveAttribute("data-turn", "candidate", { timeout: LISTENING_MS })

  return turn
}

/** A voice interview of a throwaway template (German, one of the voice languages) of 10 company
 * questions, so every draw holds all of them, its 4 multi-answer ones among them, with a
 * candidate invited, signed in on a page with a fake microphone and Mira mocked at the network
 * edge; nothing is read aloud by OpenAI. Deletes the template afterwards. */
export async function voiceInterview(
  signInAs: (email: string) => Promise<Page>,
  run: (setup: {
    candidate: Page
    token: string
    microphone: Awaited<ReturnType<typeof fakeMicrophone>>
    mira: Awaited<ReturnType<typeof fakeMira>>
  }) => Promise<void>,
  // Each question's time.
  seconds = 300,
  // Spoken answers streamed while said (fakeMira's `live`), not uploaded.
  live = false
) {
  const template = await multiAnswerTemplate(`E2E voice ${randomId()}`, 10)

  try {
    const owner = await signInAs(ownerEmail())
    const company = await createCompany(owner)
    await noReadingAloud(company.id)
    const interview = await api<{ id: string }>(
      owner,
      "POST",
      `/companies/interviews/from-template?company_id=${company.id}`,
      { template_id: template }
    )
    await api(owner, "PATCH", `/companies/interviews/${interview.id}/settings`, {
      question_seconds: seconds,
      voice: true,
    })
    const email = throwawayEmail("voice-candidate")
    await inviteCandidate(owner, interview.id, email)
    const candidate = await signInAs(email)
    const microphone = await fakeMicrophone(candidate)
    const mira = await fakeMira(candidate, live)
    await run({ candidate, token: await inviteToken(email), microphone, mira })
  } finally {
    await deleteTemplate(template)
  }
}
