import { expect, test } from "../fixtures"
import { PHONE } from "../helpers/layout"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { answered } from "../helpers/session"
import { continued, LISTENING_MS, onQuestion, voiceInterview } from "../helpers/voice-interview"

// A question's time in the test of its last moment: long enough to start listening and speak.
const ANSWER_SECONDS = 40

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
    // Listening starts once the speech detector's WebAssembly is compiled: slow on a busy stack.
    await expect(turn).toHaveAttribute("data-turn", "candidate", { timeout: LISTENING_MS })
    expect(mira.asked).toContain("question")
    const you = candidate.getByTestId("voice-heard").getByTestId("talking-dot")
    await expect(you).toHaveAttribute("data-talking", "true")
    await shot(candidate, "listening")
  })
})

// A candidate answers a multi-answer question by voice: its options carry check boxes as in
// click mode; a cough or a sound without words gets no reaction; while a slow answer is
// understood Mira thinks and says "Got it.", the options they named are picked and she asks to
// confirm; a spoken yes sends them, and she says she's moving on and reads the next question.
test("a candidate answers a voice interview's question by speaking", async ({ signInAs }) => {
  // Stepping through the draw to its multi-answer question takes a while on a busy stack.
  test.setTimeout(300_000)
  await voiceInterview(signInAs, async ({ candidate, token, microphone, mira }) => {
    // On a multi-answer question with one after it: confirming it moves on to the next.
    await onQuestion(candidate, token, true)
    const turn = await continued(candidate, token)
    const main = candidate.getByRole("main")
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
    expect(await mira.said()).not.toContain("phrases/unclear")

    // Spoken: Mira thinking while it's understood, "Got it." as the answer is slow, then two
    // options picked.
    await microphone.say()
    expect(await mira.sent()).toEqual([])
    await expect(turn).toHaveAttribute("data-turn", "thinking")
    await expect.poll(() => mira.said()).toContain("phrases/got-it")
    await shot(candidate, "thinking")
    await mira.answer({ heard: "A and B", intent: "choose", picks: [0, 1] })
    const options = main.getByRole("button", { pressed: true })
    await expect(options).toHaveCount(2)
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    await expect.poll(() => mira.said()).toContain("confirmations?picks=0&picks=1")
    await shot(candidate, "picked")
    await candidate.setViewportSize(PHONE)
    await shot(candidate, "picked-phone")
    await candidate.setViewportSize({ width: 1280, height: 800 })

    // A spoken yes confirms the choice on screen: it's sent, and the next question opens with
    // nothing picked.
    await microphone.say()
    expect(await mira.sent()).toEqual([0, 1])
    await mira.answer({ heard: "yes", intent: "confirm", picks: [] })
    await expect(options).toHaveCount(0)
    await expect.poll(async () => Number(await answered(candidate))).toBe(before + 1)
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    expect(await mira.said()).toContain("phrases/next")
    expect(mira.asked.filter((path) => path === "question")).toHaveLength(2)
  })
})

// A clear answer, one option on a single-answer question as the service decides, is saved at
// once: the option is picked, Mira says "B, saved." (fetched ahead with her other short clips),
// and the next question opens without a confirmation or "Moving on". Words she can't catch get
// "say that again" every time, not only once.
test("a clear spoken answer is saved at once", async ({ signInAs }) => {
  test.setTimeout(300_000)
  await voiceInterview(signInAs, async ({ candidate, token, microphone, mira }) => {
    await onQuestion(candidate, token, false)
    const turn = await continued(candidate, token)
    const before = Number(await answered(candidate))
    // Her short clips are in the page before she needs them.
    expect(mira.asked).toEqual(expect.arrayContaining(["phrases/unclear", "saved/1"]))

    for (let time = 0; time < 2; time++) {
      await microphone.say()
      await mira.sent()
      await mira.answer({ heard: "hmm", intent: "unclear", picks: [], clear: false })
      await expect(turn).toHaveAttribute("data-turn", "candidate")
    }

    const unclear = (await mira.said()).filter((path) => path === "phrases/unclear")
    expect(unclear).toHaveLength(2)

    await microphone.say()
    await mira.sent()
    const saved = candidate.waitForResponse(
      (response) =>
        response.request().method() === "POST" && /\/sessions\/[^/]+\/answers$/.test(response.url())
    )
    await mira.answer({ heard: "B", intent: "choose", picks: [1], clear: true })

    const answer = await saved
    expect(answer.status()).toBe(201)
    expect(answer.request().postDataJSON().option_index).toBe(1)
    await expect.poll(async () => Number(await answered(candidate))).toBe(before + 1)
    await expect.poll(() => mira.asked.filter((path) => path === "question")).toHaveLength(2)
    await expect(turn).toHaveAttribute("data-turn", "candidate")
    const said = await mira.said()
    expect(said).toContain("saved/1")
    expect(said.filter((path) => path.startsWith("confirmations"))).toEqual([])
    expect(said).not.toContain("phrases/next")
    // Nothing picked on the new question.
    await expect(candidate.getByRole("main").getByRole("button", { pressed: true })).toHaveCount(0)
  })
})

// The candidate answers in a question's last seconds and the time runs out while Mira is still
// understanding it: the screen waits for the answer, saves what it picked without asking to
// confirm, and Mira says the time is up and the answer saved. On the next question nothing is
// said: she says the time is up with no answer.
test("an answer spoken before the time runs out still counts", async ({ signInAs }) => {
  // Two questions' time run out.
  test.setTimeout(240_000)
  await voiceInterview(
    signInAs,
    async ({ candidate, token, microphone, mira }) => {
      await visit(candidate, `/invite/${token}`)
      await candidate.getByRole("checkbox").check()
      await candidate.getByTestId("voice-access").getByRole("button").click()
      await candidate.getByRole("main").getByRole("button").last().click()
      await expect(candidate).toHaveURL(/\/sessions\//)
      const turn = candidate.getByTestId("voice-turn")
      // Listening starts once the speech detector's WebAssembly is compiled: slow on a busy stack.
      await expect(turn).toHaveAttribute("data-turn", "candidate", { timeout: LISTENING_MS })
      const before = Number(await answered(candidate))

      // Spoken in time; understood only once the clock has reached zero.
      await microphone.say()
      expect(await mira.sent()).toEqual([])
      await expect(candidate.getByRole("timer")).toHaveText("0:00", {
        timeout: ANSWER_SECONDS * 1000,
      })
      expect(await mira.said()).not.toContain("phrases/time-up")
      const saved = candidate.waitForResponse(
        (response) =>
          response.request().method() === "POST" && /\/sessions\/[^/]+\/answers$/.test(response.url())
      )
      await mira.answer({ heard: "A", intent: "choose", picks: [0] })

      // Saved as the candidate's pick, not timed out.
      const answer = await saved
      expect(answer.status()).toBe(201)
      const sent = answer.request().postDataJSON()
      expect(sent.option_index ?? sent.picks).toEqual(sent.picks ? [0] : 0)
      await expect.poll(async () => Number(await answered(candidate))).toBe(before + 1)
      await expect.poll(() => mira.said()).toContain("phrases/time-up-saved")
      expect(await mira.said()).not.toContain("phrases/time-up")
      expect(mira.asked.filter((path) => path.startsWith("confirmations"))).toEqual([])

      // Silence until the next question's time runs out: no answer.
      await expect
        .poll(() => mira.asked.filter((path) => path === "question"))
        .toHaveLength(2)
      await expect(candidate.getByRole("timer")).not.toHaveText("0:00")
      await expect(candidate.getByRole("timer")).toHaveText("0:00", {
        timeout: ANSWER_SECONDS * 1000 + LISTENING_MS,
      })
      await expect.poll(() => mira.said()).toContain("phrases/time-up")
      expect((await mira.said()).filter((path) => path === "phrases/time-up-saved")).toHaveLength(1)
      expect(mira.asked.filter((path) => path.startsWith("answers"))).toHaveLength(1)
    },
    ANSWER_SECONDS
  )
})
