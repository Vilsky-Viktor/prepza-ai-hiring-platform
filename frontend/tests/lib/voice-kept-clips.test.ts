import { afterEach, beforeEach, expect, it, vi } from "vitest"

import { keptClips, savedClips } from "@/lib/voice-kept-clips"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  authHeaders: async () => ({ Authorization: "Bearer token" }),
}))

let fetches: string[]

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

  return { audio: element as unknown as HTMLAudioElement, played }
}

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

it("names the saved clips of a question's letters", () => {
  expect(savedClips(3)).toEqual(["saved/0", "saved/1", "saved/2"])
  expect(savedClips(0)).toEqual([])
})

it("fetches each clip once ahead and plays it from the page in every section", async () => {
  const clips = keptClips()
  const { audio, played } = player()
  clips.preload("section-1", ["phrases/unclear", "saved/1"])
  clips.preload("section-1", ["saved/1"])

  await clips.play(audio, "section-2/voice/saved/1")
  await clips.play(audio, "section-2/voice/saved/1")

  expect(fetches).toEqual([
    "/api/rounds/sessions/section-1/voice/phrases/unclear",
    "/api/rounds/sessions/section-1/voice/saved/1",
  ])
  expect(played).toEqual(["blob:2", "blob:2"])

  clips.release()
  await Promise.resolve()

  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:1")
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:2")
})

it("fetches a clip that isn't kept when it's played", async () => {
  const clips = keptClips()
  const { audio, played } = player()

  await clips.play(audio, "s/voice/question")

  expect(fetches).toEqual(["/api/rounds/sessions/s/voice/question"])
  expect(played).toEqual(["blob:1"])
  // Played once, never kept.
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:1")
})

it("fetches a clip again after a failed fetch", async () => {
  vi.mocked(fetch).mockResolvedValueOnce(new Response("{}", { status: 502 }))
  const clips = keptClips()

  await expect(clips.load("s", "phrases/again")).rejects.toThrow()
  await expect(clips.load("s", "phrases/again")).resolves.toBe("blob:1")

  expect(vi.mocked(fetch).mock.calls).toHaveLength(2)
})
