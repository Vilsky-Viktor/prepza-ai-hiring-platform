import { describe, expect, it } from "vitest"

import { POLL_MAX_MS, POLL_MIN_MS } from "@/config/generation"
import { nextPollDelay } from "@/lib/poll"

describe("nextPollDelay", () => {
  it("waits longer after each poll without a change", () => {
    expect(nextPollDelay(POLL_MIN_MS, false)).toBe(3000)
    expect(nextPollDelay(3000, false)).toBe(4500)
  })

  it("never waits longer than the longest", () => {
    expect(nextPollDelay(8000, false)).toBe(POLL_MAX_MS)
    expect(nextPollDelay(POLL_MAX_MS, false)).toBe(POLL_MAX_MS)
  })

  it("goes back to the shortest after a change", () => {
    expect(nextPollDelay(POLL_MAX_MS, true)).toBe(POLL_MIN_MS)
  })
})
