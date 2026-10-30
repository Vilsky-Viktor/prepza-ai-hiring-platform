import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { acknowledgement } from "@/lib/voice-acknowledgement"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  authHeaders: async () => ({ Authorization: "Bearer token" }),
}))

/** An audio element that ends each clip at once and records what it played. */
function player() {
  const played: string[] = []
  const element = {
    src: "",
    error: null,
    onended: null as (() => void) | null,
    onerror: null as (() => void) | null,
    play: vi.fn(async () => {
      played.push(element.src)
      queueMicrotask(() => element.onended?.())
    }),
  }

  return { element: element as unknown as HTMLAudioElement, played }
}

describe("Mira's acknowledgement", () => {
  let fetches: string[]

  beforeEach(() => {
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
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it("is fetched once and replayed from the same address in every section", async () => {
    const said = acknowledgement()
    const { element, played } = player()

    await said.play(element, "section-1", 800)
    await said.play(element, "section-2", 800)

    expect(fetches).toEqual([
      "/api/rounds/sessions/section-1/voice/phrases/got-it",
    ])
    expect(played).toEqual(["blob:1", "blob:1"])

    said.release()
    await Promise.resolve()

    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:1")
  })

  it("never fails the answer, and is fetched again after a failed fetch", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined)
    vi.mocked(fetch).mockResolvedValueOnce(new Response("{}", { status: 502 }))
    const said = acknowledgement()
    const { element, played } = player()

    await expect(said.play(element, "s", 800)).resolves.toBeUndefined()
    await said.play(element, "s", 800)

    expect(vi.mocked(fetch).mock.calls).toHaveLength(2)
    expect(played).toEqual(["blob:1"])
  })

  it("isn't said after a sound too short to be words, such as a cough", async () => {
    const said = acknowledgement()
    const { element, played } = player()

    await said.play(element, "s", 200)

    expect(fetches).toEqual([])
    expect(played).toEqual([])
  })
})
