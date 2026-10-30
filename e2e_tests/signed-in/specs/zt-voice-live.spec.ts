import { expect, test } from "../fixtures"
import { answered } from "../helpers/session"
import { continued, onQuestion, voiceInterview } from "../helpers/voice-interview"

// A sentence of the fake microphone's speech at 16-bit PCM, 16 kHz: at least a second of it.
const A_SECOND = 32_000
// Seconds a question has, so none times out while the test speaks.
const SECONDS = 300

// Live listening: a spoken answer streams to the service while the candidate speaks, from just
// before they started, and its answer comes back over the stream, with no recording uploaded.
// When the stream drops mid-answer, the page sends the recording instead and acts on that answer
// the same way.
test("a spoken answer is heard live, and sent whole when the stream drops", async ({
  signInAs,
}) => {
  test.setTimeout(300_000)
  await voiceInterview(
    signInAs,
    async ({ candidate, token, microphone, mira }) => {
      await onQuestion(candidate, token, false)
      const turn = await continued(candidate, token)
      const before = Number(await answered(candidate))

      // Streamed while spoken, then answered over the stream: saved at once.
      await microphone.say()
      expect(await mira.sent()).toEqual([])
      expect(Math.max(...mira.streamed())).toBeGreaterThan(A_SECOND)
      await mira.answer({ heard: "B", intent: "choose", picks: [1], clear: true })
      await expect.poll(async () => Number(await answered(candidate))).toBe(before + 1)
      await expect.poll(() => mira.said()).toContain("saved/1")
      expect(mira.asked.filter((path) => path.startsWith("answers"))).toEqual([])

      // The next question: the stream drops while the candidate speaks, so the recording is
      // uploaded and its answer acted on: words Mira couldn't catch, so she asks again.
      await expect.poll(() => mira.asked.filter((path) => path === "question")).toHaveLength(2)
      await expect(turn).toHaveAttribute("data-turn", "candidate")
      await microphone.say()
      await mira.dropStream()
      await mira.sent()
      expect(mira.asked.filter((path) => path.startsWith("answers"))).toHaveLength(1)
      await mira.answer({ heard: "hmm", intent: "unclear", picks: [], clear: false })
      await expect.poll(() => mira.said()).toContain("phrases/unclear")
      await expect(turn).toHaveAttribute("data-turn", "candidate")
    },
    SECONDS,
    true
  )
})
