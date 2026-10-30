import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany, inviteCandidate } from "../helpers/api"
import { inviteToken } from "../helpers/db"
import { deleteTemplate, multiAnswerTemplate } from "../helpers/db-library"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { answered } from "../helpers/session"
import { ownerEmail, randomId, throwawayEmail } from "../helpers/users"
import { fakeMicrophone, fakeMira, noReadingAloud } from "../helpers/voice"

type Step = {
  session: { id: string; answered: number; total: number }
  question: { question_id: string; multi: boolean } | null
}

/** A voice interview of a throwaway template (German, one of the voice languages), with a
 * candidate invited, signed in on a page with a fake microphone and Mira mocked at the network
 * edge; nothing is read aloud by OpenAI. Deletes the template afterwards. */
async function voiceInterview(
  signInAs: (email: string) => Promise<Page>,
  run: (setup: {
    candidate: Page
    token: string
    microphone: Awaited<ReturnType<typeof fakeMicrophone>>
    mira: Awaited<ReturnType<typeof fakeMira>>
  }) => Promise<void>
) {
  const template = await multiAnswerTemplate(`E2E voice ${randomId()}`)

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
      question_seconds: 300,
      voice: true,
    })
    const email = throwawayEmail("voice-candidate")
    await inviteCandidate(owner, interview.id, email)
    const candidate = await signInAs(email)
    const microphone = await fakeMicrophone(candidate)
    const mira = await fakeMira(candidate)
    await run({ candidate, token: await inviteToken(email), microphone, mira })
  } finally {
    await deleteTemplate(template)
  }
}

// A voice interview's start page asks for the microphone and sound first: the start works only
// once they're allowed. Refused, the step says so and offers to try again; allowed, the
// interview opens with Mira reading the question, then listening.
test("a candidate allows the microphone before a voice interview starts", async ({
  signInAs,
}) => {
  await voiceInterview(signInAs, async ({ candidate, token, microphone, mira }) => {
    await visit(candidate, `/invite/${token}`)
    const access = candidate.getByTestId("voice-access")
    const start = candidate.getByRole("main").getByRole("button").last()
    await expect(access).toHaveAttribute("data-access", "ask")
    await candidate.getByRole("checkbox").check()
    await expect(start).toBeDisabled()

    // Refused: no start, and the button asks again.
    await microphone.deny(true)
    await access.getByRole("button").click()
    await expect(access).toHaveAttribute("data-access", "denied")
    await expect(start).toBeDisabled()
    await shot(candidate, "access-denied")

    // Allowed: the start works.
    await microphone.deny(false)
    await access.getByRole("button").click()
    await expect(access).toHaveAttribute("data-access", "granted")
    await expect(start).toBeEnabled()
    await candidate.setViewportSize(PHONE)
    await shot(candidate, "access-granted-phone")
    await candidate.setViewportSize({ width: 1280, height: 800 })
    await start.click()
    await expect(candidate).toHaveURL(/\/sessions\//)

    // Mira reads the question, then it's the candidate's turn.
    const turn = candidate.getByTestId("voice-turn")
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    expect(mira.asked).toContain("question")
    const you = candidate.getByTestId("voice-heard").getByTestId("talking-dot")
    await expect(you).toHaveAttribute("data-talking", "true")
    await shot(candidate, "listening")
  })
})

// A candidate answers a multi-answer question by voice: its options carry check boxes as in
// click mode; a cough or a sound without words gets no reaction; Mira says "Got it." as they stop speaking and thinks while the answer is
// understood, the options they named are picked and she asks to confirm; a spoken yes sends
// them, and she says she's moving on and reads the next question.
test("a candidate answers a voice interview's question by speaking", async ({ signInAs }) => {
  // Stepping through the draw to its multi-answer question takes a while on a busy stack.
  test.setTimeout(300_000)
  await voiceInterview(signInAs, async ({ candidate, token, microphone, mira }) => {
    // Started, and on to a multi-answer question of the draw that isn't its last, as the player
    // does.
    const { sessions } = await api<{ sessions: { id: string }[] }>(
      candidate,
      "POST",
      `/companies/invites/${token}/start`,
      { pledged: true }
    )

    for (;;) {
      const step = await api<Step>(candidate, "POST", `/rounds/sessions/${sessions[0].id}/step`)
      expect(step.question, "the draw holds a multi-answer question").not.toBeNull()

      // One with a question after it: confirming it moves on to the next.
      if (step.question!.multi && step.session.answered + 1 < step.session.total) {
        break
      }

      await api(candidate, "POST", `/rounds/sessions/${step.session.id}/answers`, {
        question_id: step.question!.question_id,
        option_index: 0,
      })
    }

    // Continued from the invite, the microphone allowed first.
    await visit(candidate, `/invite/${token}`)
    await candidate.getByTestId("voice-access").getByRole("button").click()
    await candidate.getByRole("main").getByRole("button").last().click()
    await expect(candidate).toHaveURL(/\/sessions\//)
    const main = candidate.getByRole("main")
    const turn = candidate.getByTestId("voice-turn")
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    await expect(candidate.getByTestId("multi-choice").filter({ visible: true })).toBeVisible()
    await expect(candidate.getByTestId("option-check")).toHaveCount(4)
    const before = Number(await answered(candidate))

    // A cough is no speech: nothing is sent until the candidate speaks. What the service hears
    // as no words at all is ignored: no "didn't catch that", and Mira listens on.
    await microphone.say(true)
    expect(await mira.sent()).toEqual([])
    expect(await microphone.sentDuring()).not.toContain("cough")
    await mira.answer({ heard: "", intent: "noise", picks: [] })
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    expect(mira.asked.filter((path) => path.startsWith("phrases/unclear"))).toEqual([])

    // Spoken: "Got it.", Mira thinking while it's understood, then two options picked.
    await microphone.say()
    expect(await mira.sent()).toEqual([])
    await expect(turn).toHaveAttribute("data-turn", "thinking")
    expect(mira.asked).toContain("phrases/got-it")
    await shot(candidate, "thinking")
    await mira.answer({ heard: "A and B", intent: "choose", picks: [0, 1] })
    const options = main.getByRole("button", { pressed: true })
    await expect(options).toHaveCount(2)
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    expect(mira.asked).toContain("confirmations?picks=0&picks=1")
    await shot(candidate, "picked")
    await candidate.setViewportSize(PHONE)
    await shot(candidate, "picked-phone")
    await candidate.setViewportSize({ width: 1280, height: 800 })

    // A spoken yes confirms the choice on screen: it's sent, and the next question opens.
    await microphone.say()
    expect(await mira.sent()).toEqual([0, 1])
    await mira.answer({ heard: "yes", intent: "confirm", picks: [] })
    await expect(candidate.getByTestId("option-check")).toHaveCount(0)
    await expect.poll(async () => Number(await answered(candidate))).toBe(before + 1)
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    expect(mira.asked).toContain("phrases/next")
    expect(mira.asked.filter((path) => path === "question")).toHaveLength(2)
  })
})
