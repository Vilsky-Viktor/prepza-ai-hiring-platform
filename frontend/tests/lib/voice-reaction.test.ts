import { expect, it, vi } from "vitest"

import { type Mira, react } from "@/lib/voice-reaction"
import type { VoiceAnswer } from "@/types/round"

function mira(sent = true): Mira {
  return {
    sessionId: "s1",
    questionId: "q1",
    handlers: {
      onPick: vi.fn(),
      onConfirm: vi.fn(async () => sent),
      onSave: vi.fn(async () => sent),
      failedMessage: "",
    },
    confirmed: { current: false },
    say: vi.fn(async () => undefined),
    listen: vi.fn(),
  }
}

function answer(intent: VoiceAnswer["intent"], picks: number[] = []) {
  return { heard: "", intent, picks, clear: false }
}

it("ignores an answer with no words and listens on", async () => {
  const her = mira()
  await react(answer("noise"), her)

  expect(her.listen).toHaveBeenCalledOnce()
  expect(her.say).not.toHaveBeenCalled()
})

it("picks a choice on screen and asks to confirm it", async () => {
  const her = mira()
  await react(answer("choose", [0, 2]), her)

  expect(her.handlers.onPick).toHaveBeenCalledWith("q1", [0, 2])
  expect(her.say).toHaveBeenCalledWith("s1/voice/confirmations?picks=0&picks=2")
})

it.each([
  [true, 0],
  [false, 1],
])(
  "saves a clear choice at once without asking (sent: %s), listening on when it wasn't",
  async (sent, listened) => {
    const her = mira(sent)
    await react({ ...answer("choose", [1]), clear: true }, her)

    expect(her.handlers.onPick).toHaveBeenCalledWith("q1", [1])
    expect(her.handlers.onSave).toHaveBeenCalledWith([1])
    expect(her.say).not.toHaveBeenCalled()
    expect(her.confirmed.current).toBe(true)
    expect(her.listen).toHaveBeenCalledTimes(listened)
  }
)

it.each([
  [true, 0],
  [false, 1],
])(
  "sends the choice on a yes (sent: %s), listening on when it wasn't",
  async (sent, listened) => {
    const her = mira(sent)
    await react(answer("confirm", [1]), her)

    expect(her.handlers.onConfirm).toHaveBeenCalledOnce()
    expect(her.confirmed.current).toBe(true)
    expect(her.listen).toHaveBeenCalledTimes(listened)
  }
)

it("asks again every time it's told no or can't catch the answer", async () => {
  const her = mira()
  await react(answer("reject"), her)
  await react(answer("unclear"), her)
  await react(answer("unclear"), her)

  expect(vi.mocked(her.say).mock.calls).toEqual([
    ["s1/voice/phrases/again"],
    ["s1/voice/phrases/unclear"],
    ["s1/voice/phrases/unclear"],
  ])
  expect(her.listen).not.toHaveBeenCalled()
})
