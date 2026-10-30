import { describe, expect, it } from "vitest"

import { YOU_WAVE_FLOOR } from "@/config/voice"
import { voiceHeight } from "@/hooks/use-voice-waves"

describe("voiceHeight", () => {
  it("leaves the candidate's wave flat under room noise", () => {
    expect(voiceHeight(0)).toBe(0)
    expect(voiceHeight(YOU_WAVE_FLOOR / 2)).toBe(0)
  })

  it("grows with the voice, a loud one less than in step", () => {
    const quiet = voiceHeight(0.01)
    const loud = voiceHeight(0.04)

    expect(quiet).toBeGreaterThan(0)
    expect(loud).toBeGreaterThan(quiet)
    expect(loud).toBeCloseTo(quiet * 2)
  })
})
