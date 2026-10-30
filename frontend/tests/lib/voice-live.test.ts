import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  LIVE_ANSWER_WAIT_MS,
  LIVE_MAX_FAILURES,
  LIVE_RENEW_MS,
} from "@/config/voice"
import { sendSpokenAnswer } from "@/lib/voice-clips"
import { liveListening, pcm16 } from "@/lib/voice-live"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  idToken: async () => "token",
}))

vi.mock("@/lib/voice-clips", () => ({ sendSpokenAnswer: vi.fn() }))

const ANSWER = { heard: "B", intent: "choose", picks: [1], clear: true }
const UPLOADED = {
  answer: { heard: "C", intent: "choose", picks: [2], clear: true },
  stages: { transcribe: 2000 },
}

let sockets: FakeSocket[]

class FakeSocket {
  static OPEN = 1
  url: string
  binaryType = ""
  sent: (string | ArrayBuffer)[] = []
  closed = false
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    sockets.push(this)
  }

  send(data: string | ArrayBuffer) {
    this.sent.push(data)
  }

  close() {
    this.closed = true
  }

  // The service's side.
  opened() {
    this.onopen?.()
  }

  says(message: object) {
    this.onmessage?.({ data: JSON.stringify(message) })
  }

  ends() {
    this.onclose?.()
  }

  // What was sent: steps as objects, audio as its byte count.
  messages() {
    return this.sent.map((data) =>
      typeof data === "string" ? JSON.parse(data) : data.byteLength
    )
  }
}

function listening() {
  const latest = { current: { sessionId: "s1", chosen: [2] } }

  return liveListening(latest)
}

// Lets the socket's sign-in (an awaited token) finish.
const settled = () => new Promise((done) => setTimeout(done, 0))

beforeEach(() => {
  sockets = []
  vi.stubGlobal("WebSocket", FakeSocket)
  vi.stubGlobal("window", {
    location: { protocol: "https:", host: "prepza.test" },
  })
  vi.mocked(sendSpokenAnswer).mockResolvedValue(
    UPLOADED as Awaited<ReturnType<typeof sendSpokenAnswer>>
  )
})

afterEach(() => {
  vi.useRealTimers()
})

describe("pcm16", () => {
  it("turns the detector's samples into 16-bit PCM, clipping what's too loud", () => {
    const pcm = new Int16Array(pcm16(new Float32Array([0, 0.5, -1, 2, -2])))

    expect([...pcm]).toEqual([0, 16383, -32768, 32767, -32768])
  })
})

describe("liveListening", () => {
  it("signs in first, then sends the speech in order, and gives the answer heard live", async () => {
    const live = listening()
    live.open()
    const [socket] = sockets
    // Speech heard before the connection is open waits for it.
    live.start([new Float32Array(512), new Float32Array(512)])
    live.frame(new Float32Array(512))
    socket.opened()
    await settled()
    socket.says({ type: "ready" })
    live.end()
    socket.says({ type: "answer", answer: ANSWER, stages: { total: 900 } })

    const understood = await live.answer(new Blob(["sound"]))

    expect(socket.url).toBe(
      "wss://prepza.test/api/rounds/sessions/s1/voice/stream"
    )
    expect(socket.messages()).toEqual([
      { token: "token" },
      { type: "start" },
      1024,
      1024,
      1024,
      { type: "end", waiting: [2] },
    ])
    expect(understood).toEqual({
      answer: ANSWER,
      stages: { total: 900 },
      live: true,
    })
    expect(sendSpokenAnswer).not.toHaveBeenCalled()
    expect(socket.closed).toBe(true)
  })

  it("sends the recording whole when the connection drops mid-answer", async () => {
    const live = listening()
    live.open()
    const [socket] = sockets
    socket.opened()
    await settled()
    socket.says({ type: "ready" })
    live.start([new Float32Array(512)])
    socket.ends()
    live.frame(new Float32Array(512))
    live.end()
    const recording = new Blob(["sound"])

    const understood = await live.answer(recording)

    expect(understood).toEqual({ ...UPLOADED, live: false })
    expect(sendSpokenAnswer).toHaveBeenCalledWith("s1", recording, [2])
    // Nothing more went out once it dropped.
    expect(socket.messages()).toEqual([
      { token: "token" },
      { type: "start" },
      1024,
    ])
  })

  it("sends the recording whole when the service gives no answer in time", async () => {
    vi.useFakeTimers()
    const live = listening()
    live.open()
    const [socket] = sockets
    socket.opened()
    await vi.advanceTimersByTimeAsync(0)
    live.start([new Float32Array(512)])
    live.end()
    const understood = live.answer(new Blob(["sound"]))
    await vi.advanceTimersByTimeAsync(LIVE_ANSWER_WAIT_MS)

    expect(await understood).toEqual({ ...UPLOADED, live: false })
    expect(socket.closed).toBe(true)
  })

  it("sends the recording whole when no connection was open", async () => {
    const live = listening()
    live.end()

    expect(await live.answer(new Blob(["sound"]))).toEqual({
      ...UPLOADED,
      live: false,
    })
  })

  it("renews a quiet connection, never one carrying speech", async () => {
    vi.useFakeTimers()
    const live = listening()
    live.open()
    await vi.advanceTimersByTimeAsync(LIVE_RENEW_MS)

    expect(sockets).toHaveLength(2)
    expect(sockets[0].closed).toBe(true)

    live.start([new Float32Array(512)])
    await vi.advanceTimersByTimeAsync(LIVE_RENEW_MS)

    expect(sockets).toHaveLength(2)
  })

  it("stops opening connections after several in a row never got ready", () => {
    const live = listening()

    for (let attempt = 0; attempt < LIVE_MAX_FAILURES; attempt++) {
      live.open()
      sockets.at(-1)?.ends()
    }

    live.open()

    expect(sockets).toHaveLength(LIVE_MAX_FAILURES)
  })

  it("closes the connection when listening stops", () => {
    const live = listening()
    live.open()
    live.close()

    expect(sockets[0].closed).toBe(true)
  })
})
