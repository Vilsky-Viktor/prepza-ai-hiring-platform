import { describe, expect, it } from "vitest"

import { sendPicks, toggled } from "@/hooks/use-session-answers"
import type { AnswerInput } from "@/types/round"

/** What `then` was told about the picks sent, and whether it ran, when saving returns `saves`. */
async function sent(picks: number[], saves: boolean, always = false) {
  const answers: AnswerInput[] = []
  const told: boolean[] = []
  const done = await sendPicks(
    picks,
    false,
    async (input) => {
      answers.push(input)

      return saves
    },
    async (saved) => {
      told.push(saved)
    },
    always
  )

  return { answers, told, done }
}

describe("sendPicks", () => {
  it("tells `then` a pick was saved", async () => {
    expect(await sent([2], true)).toEqual({
      answers: [{ option_index: 2 }],
      told: [true],
      done: true,
    })
  })

  it("tells `then` nothing was saved when there was no pick", async () => {
    expect(await sent([], true)).toEqual({
      answers: [],
      told: [false],
      done: true,
    })
  })

  it("tells `then` nothing was saved when saving failed and it moves on anyway", async () => {
    expect(await sent([1], false, true)).toEqual({
      answers: [{ option_index: 1 }],
      told: [false],
      done: true,
    })
  })

  it("doesn't do `then` when saving failed", async () => {
    expect(await sent([1], false)).toEqual({
      answers: [{ option_index: 1 }],
      told: [],
      done: false,
    })
  })
})

describe("toggled", () => {
  it("makes a tapped option the pick of a one-answer question", () => {
    expect(toggled([], 2, false)).toEqual([2])
    expect(toggled([2], 0, false)).toEqual([0])
    expect(toggled([2], 2, false)).toEqual([2])
  })

  it("ticks and unticks each option of a multi-answer question on its own", () => {
    expect(toggled([], 1, true)).toEqual([1])
    expect(toggled([1], 3, true)).toEqual([1, 3])
    expect(toggled([1, 3], 1, true)).toEqual([3])
  })
})
