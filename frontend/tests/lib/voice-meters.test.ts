import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { SOUND_WAIT_MS } from "@/config/voice"
import { soundAllowed } from "@/lib/voice-meters"

/** An audio context in `state`, whose resume starts it only if `starts`. */
function context(state: AudioContextState, starts: boolean) {
  const fake = {
    state,
    resume: vi.fn(() => {
      if (starts) {
        fake.state = "running"

        return Promise.resolve()
      }

      // A browser holding sound back until a tap never settles the resume.
      return new Promise<void>(() => undefined)
    }),
  }

  return fake
}

describe("soundAllowed", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal("window", globalThis)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("allows a context already playing", async () => {
    const running = context("running", false)

    await expect(
      soundAllowed(running as unknown as AudioContext)
    ).resolves.toBe(true)
    expect(running.resume).not.toHaveBeenCalled()
  })

  it("allows a suspended context the browser lets start", async () => {
    const suspended = context("suspended", true)

    await expect(
      soundAllowed(suspended as unknown as AudioContext)
    ).resolves.toBe(true)
  })

  it("gives up after a short wait when the browser needs a tap first", async () => {
    const held = soundAllowed(
      context("suspended", false) as unknown as AudioContext
    )
    await vi.advanceTimersByTimeAsync(SOUND_WAIT_MS)

    await expect(held).resolves.toBe(false)
  })
})
