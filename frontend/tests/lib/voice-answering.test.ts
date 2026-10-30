import { afterEach, beforeEach, expect, it, vi } from "vitest"

import { answerInProgress } from "@/lib/voice-answering"
import type { VoiceAnswer } from "@/types/round"

const HOLD_MS = 10_000

beforeEach(() => {
  vi.useFakeTimers()
  vi.stubGlobal("window", globalThis)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

function answer(intent: VoiceAnswer["intent"], picks: number[] = []) {
  return { heard: "", intent, picks, clear: false }
}

it.each([
  ["a choice", answer("choose", [1, 2]), [1, 2]],
  ["a yes to the choice waiting", answer("confirm", [0]), [0]],
  ["words she didn't catch", answer("unclear"), null],
  ["no words at all", answer("noise"), null],
  ["a failure", null, null],
])(
  "waits at the time-up for an answer begun in time: %s",
  async (_, understood, picks) => {
    const inProgress = answerInProgress()
    inProgress.begin()
    const held = inProgress.timeUp(HOLD_MS)
    await vi.advanceTimersByTimeAsync(HOLD_MS / 2)
    inProgress.end(understood)

    expect(await held).toEqual(picks)
    expect(inProgress.timedOut()).toBe(true)
  }
)

it("gives up waiting after the hold", async () => {
  const inProgress = answerInProgress()
  inProgress.begin()
  const held = inProgress.timeUp(HOLD_MS)
  await vi.advanceTimersByTimeAsync(HOLD_MS)

  expect(await held).toBeNull()
})

it("doesn't wait when nothing was being said or understood", async () => {
  const inProgress = answerInProgress()

  expect(inProgress.timedOut()).toBe(false)
  expect(await inProgress.timeUp(HOLD_MS)).toBeNull()

  inProgress.begin()
  inProgress.end(answer("choose", [1]))

  expect(await inProgress.timeUp(HOLD_MS)).toBeNull()
})
