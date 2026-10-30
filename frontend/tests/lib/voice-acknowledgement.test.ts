import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ACK_DELAY_MS } from "@/config/voice"
import { acknowledgement } from "@/lib/voice-acknowledgement"
import { keptClips } from "@/lib/voice-kept-clips"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  authHeaders: async () => ({ Authorization: "Bearer token" }),
}))

/** An audio element that records what it played and keeps playing until paused. */
function player() {
  const played: string[] = []
  const element = {
    src: "",
    error: null,
    onended: null as (() => void) | null,
    onerror: null as (() => void) | null,
    play: vi.fn(async () => {
      played.push(element.src)
    }),
    pause: vi.fn(),
  }

  return { element, audio: element as unknown as HTMLAudioElement, played }
}

describe("Mira's acknowledgement", () => {
  let fetches: string[]

  beforeEach(() => {
    vi.useFakeTimers()
    fetches = []
    let made = 0
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        fetches.push(url)

        return new Response("OggS", { status: 200 })
      })
    )
    vi.spyOn(URL, "createObjectURL").mockImplementation(() => `blob:${++made}`)
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it("isn't said when the answer is back in time", async () => {
    const said = acknowledgement(keptClips())
    const { audio, played } = player()

    said.schedule(audio, "s", 800)
    said.cancel(audio)
    await vi.advanceTimersByTimeAsync(ACK_DELAY_MS * 2)

    expect(played).toEqual([])
  })

  it("fills a slow answer's wait and stops the moment it's back", async () => {
    const clips = keptClips()
    const said = acknowledgement(clips)
    const { element, audio, played } = player()

    said.schedule(audio, "section-1", 800)
    await vi.advanceTimersByTimeAsync(ACK_DELAY_MS)
    said.cancel(audio)

    expect(fetches).toEqual([
      "/api/rounds/sessions/section-1/voice/phrases/got-it",
    ])
    expect(played).toEqual(["blob:1"])
    expect(element.pause).toHaveBeenCalledOnce()
  })

  it("isn't said after a sound too short to be words, such as a cough", async () => {
    const said = acknowledgement(keptClips())
    const { audio, played } = player()

    said.schedule(audio, "s", 200)
    await vi.advanceTimersByTimeAsync(ACK_DELAY_MS * 2)

    expect(fetches).toEqual([])
    expect(played).toEqual([])
  })
})
