import * as Sentry from "@sentry/nextjs"
import { afterEach, beforeEach, expect, it, vi } from "vitest"

import { serverStages, turnTiming } from "@/lib/voice-timing"

vi.mock("@sentry/nextjs", () => ({ metrics: { distribution: vi.fn() } }))

const ANSWER = {
  heard: "B",
  intent: "choose" as const,
  picks: [1],
  clear: true,
}
const ATTRIBUTES = { intent: "choose", clear: true }

let now: number

beforeEach(() => {
  now = 1000
  vi.spyOn(performance, "now").mockImplementation(() => now)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.mocked(Sentry.metrics.distribution).mockClear()
})

function sent() {
  return vi
    .mocked(Sentry.metrics.distribution)
    .mock.calls.map(([name, value, options]) => [
      name,
      value,
      options?.attributes,
    ])
}

it.each([
  [
    "transcribe;dur=812, match;dur=3, total;dur=840",
    { transcribe: 812, match: 3, total: 840 },
  ],
  ['match;desc="model";dur=12', { match: 12 }],
  ["total", {}],
  [null, {}],
])("reads the service's stages from %j", (header, stages) => {
  expect(serverStages(header)).toEqual(stages)
})

it("times a turn from the speech's end to the answer and to Mira's reaction", () => {
  const timing = turnTiming()
  timing.ended()
  now = 3400
  timing.answered(ANSWER, { transcribe: 2000, match: 0 })
  now = 3500
  timing.reacted()
  // A second clip is no reaction to the same answer.
  timing.reacted()

  expect(sent()).toEqual([
    ["voice.answer.response", 2400, ATTRIBUTES],
    ["voice.answer.transcribe", 2000, ATTRIBUTES],
    ["voice.answer.match", 0, ATTRIBUTES],
    ["voice.answer.reaction", 2500, ATTRIBUTES],
  ])
})

it("reports no reaction for an answer Mira said nothing to", () => {
  const timing = turnTiming()
  timing.ended()
  timing.answered(ANSWER, {})
  timing.dropped()
  timing.reacted()

  expect(sent().map(([name]) => name)).toEqual(["voice.answer.response"])
})

it("reports nothing for a clip that follows no answer", () => {
  const timing = turnTiming()
  timing.answered(ANSWER, {})
  timing.reacted()

  expect(sent()).toEqual([])
})
