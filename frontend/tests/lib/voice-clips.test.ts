import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/lib/api"
import {
  clipUrl,
  playClip,
  prepareNextQuestion,
  sendSpokenAnswer,
} from "@/lib/voice-clips"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  authHeaders: async () => ({ Authorization: "Bearer token" }),
}))

let calls: [string, RequestInit][]

function replying(response: () => Response) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit) => {
      calls.push([url, init])

      return response()
    })
  )
}

beforeEach(() => {
  calls = []
  vi.spyOn(URL, "createObjectURL").mockImplementation(() => "blob:clip")
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("clipUrl", () => {
  it("fetches a clip signed in and gives it as an address to play", async () => {
    replying(() => new Response("OggS"))

    await expect(clipUrl("s-1/voice/question")).resolves.toBe("blob:clip")
    expect(calls[0][0]).toBe("/api/rounds/sessions/s-1/voice/question")
    expect(calls[0][1].headers).toEqual({ Authorization: "Bearer token" })
  })

  it("fails with the service's message", async () => {
    replying(() =>
      Response.json(
        { detail: "Couldn't read the question aloud." },
        { status: 502 }
      )
    )

    const error = await clipUrl("s-1/voice/question").catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(502)
    expect(error.message).toBe("Couldn't read the question aloud.")
  })
})

describe("playClip", () => {
  it("resolves once the clip has played, then frees its address", async () => {
    replying(() => new Response("OggS"))
    const player = {
      src: "",
      onended: null as (() => void) | null,
      onerror: null,
      play: vi.fn(async () => {
        queueMicrotask(() => player.onended?.())
      }),
    }

    await playClip(player as unknown as HTMLAudioElement, "s-1/voice/question")

    expect(player.src).toBe("blob:clip")
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:clip")
  })

  it("rejects when the browser won't play it, and still frees its address", async () => {
    replying(() => new Response("OggS"))
    const player = {
      src: "",
      play: vi.fn(async () => {
        throw new Error("NotAllowedError")
      }),
    }

    await expect(
      playClip(player as unknown as HTMLAudioElement, "s-1/voice/question")
    ).rejects.toThrow("NotAllowedError")
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:clip")
  })
})

describe("sendSpokenAnswer", () => {
  it("sends the recording with the choice on screen, and gives what it meant", async () => {
    const answer = { heard: "the median", intent: "choose", picks: [1] }
    replying(() => Response.json(answer))
    const audio = new Blob(["sound"], { type: "audio/webm" })

    await expect(sendSpokenAnswer("s-1", audio, [0, 2])).resolves.toEqual(
      answer
    )
    expect(calls[0][0]).toBe(
      "/api/rounds/sessions/s-1/voice/answers?waiting=0&waiting=2"
    )
    expect(calls[0][1].method).toBe("POST")
    expect(calls[0][1].headers).toEqual({
      Authorization: "Bearer token",
      "Content-Type": "audio/webm",
    })
    expect(calls[0][1].body).toBe(audio)
  })

  it("fails with the service's refusal", async () => {
    replying(() =>
      Response.json(
        {
          detail:
            "Couldn't hear the answer.\nPlease try again or tap an option.",
        },
        { status: 502 }
      )
    )

    await expect(
      sendSpokenAnswer("s-1", new Blob(["sound"]), [])
    ).rejects.toThrow(
      "Couldn't hear the answer.\nPlease try again or tap an option."
    )
  })
})

describe("prepareNextQuestion", () => {
  it("asks for the next question to be read ahead, and ignores a failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        calls.push([url, init])

        throw new Error("offline")
      })
    )

    prepareNextQuestion("section-1")
    await vi.waitFor(() => expect(calls).toHaveLength(1))

    expect(calls[0][0]).toBe(
      "/api/rounds/sessions/section-1/voice/next-question/prepare"
    )
    expect(calls[0][1].method).toBe("POST")
    expect(calls[0][1].headers).toEqual({ Authorization: "Bearer token" })
  })
})
