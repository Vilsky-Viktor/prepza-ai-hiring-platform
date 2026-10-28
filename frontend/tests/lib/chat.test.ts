import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/lib/api"
import {
  StreamError,
  startHelpChat,
  streamEvents,
  streamHelp,
} from "@/lib/chat"

// No Firebase in a unit test: nobody is signed in.
vi.mock("@/lib/firebase", () => ({
  firebaseAuth: async () => ({
    authStateReady: async () => {},
    currentUser: null,
  }),
}))

/** A streamed 200 answer that sends `chunks` one by one, as the network may split them. */
function streamed(chunks: string[]) {
  const encoder = new TextEncoder()
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }

      controller.close()
    },
  })

  return new Response(body, {
    headers: { "Content-Type": "text/event-stream" },
  })
}

/** The deltas the help chat gets from the answer. */
async function deltas(response: Response) {
  vi.mocked(fetch).mockResolvedValue(response)
  const got: string[] = []
  await streamHelp(
    [],
    (event) => event.delta && got.push(event.delta),
    new AbortController().signal
  )

  return got
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn())
  vi.stubGlobal("document", { documentElement: { lang: "en" } })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("streamHelp", () => {
  it("posts the conversation to the help chat", async () => {
    await deltas(streamed([]))

    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe("/api/assistant/help/chat")
    expect(init?.method).toBe("POST")
    expect(JSON.parse(String(init?.body))).toMatchObject({ messages: [] })
  })

  it("names the conversation, and a new chat with a new id", async () => {
    const chatIds = async () => {
      vi.mocked(fetch).mockResolvedValue(streamed([]))
      await streamHelp([], () => {}, new AbortController().signal)

      return JSON.parse(String(vi.mocked(fetch).mock.lastCall?.[1]?.body))
        .chat_id
    }
    const first = await chatIds()
    const again = await chatIds()
    startHelpChat()
    const next = await chatIds()

    expect(first).toBe(again)
    expect(next).not.toBe(first)
  })

  it("passes each event's delta on, in order", async () => {
    const got = await deltas(
      streamed(['data: {"delta":"Hel"}\n\n', 'data: {"delta":"lo"}\n\n'])
    )

    expect(got).toEqual(["Hel", "lo"])
  })

  it("joins an event split across chunks", async () => {
    const got = await deltas(
      streamed(['data: {"del', 'ta":"one"}\n', '\ndata: {"delta":"two"}\n\n'])
    )

    expect(got).toEqual(["one", "two"])
  })

  it("reads CRLF and CR line ends like LF", async () => {
    const got = await deltas(
      streamed(['data: {"delta":"a"}\r\n\r\n', 'data: {"delta":"b"}\r\r'])
    )

    expect(got).toEqual(["a", "b"])
  })

  it("skips comments, other fields and empty events", async () => {
    const got = await deltas(
      streamed([
        ": keep-alive\n\n",
        'event: message\nid: 1\ndata: {"delta":"x"}\n\n',
        "retry: 1000\n\n",
        'data: {"done":true}\n\n',
      ])
    )

    expect(got).toEqual(["x"])
  })

  it("joins an event's data lines with new lines", async () => {
    const got = await deltas(streamed(['data: {"delta":\ndata:"multi"}\n\n']))

    expect(got).toEqual(["multi"])
  })

  it("ignores an event the stream ends in the middle of", async () => {
    const got = await deltas(
      streamed(['data: {"delta":"kept"}\n\n', 'data: {"delta":"cut"}'])
    )

    expect(got).toEqual(["kept"])
  })

  it("throws an error event's message", async () => {
    const response = streamed([
      'data: {"delta":"a"}\n\n',
      'data: {"error":"Too many messages"}\n\n',
    ])

    await expect(deltas(response)).rejects.toThrow("Too many messages")
  })

  it("throws the API's detail with the status when the request fails", async () => {
    const response = Response.json({ detail: "Paused" }, { status: 503 })
    const failed = deltas(response)

    await expect(failed).rejects.toBeInstanceOf(ApiError)
    await expect(failed).rejects.toMatchObject({
      status: 503,
      message: "Paused",
    })
  })

  it("names the status when a failed answer has no detail", async () => {
    const response = new Response("oops", { status: 500 })

    await expect(deltas(response)).rejects.toThrow(
      "Chat failed with status 500"
    )
  })
})

describe("streamEvents", () => {
  it("passes every event's data on, and an error event's code with its message", async () => {
    vi.mocked(fetch).mockResolvedValue(
      streamed([
        'data: {"conversation":{"id":"c1"}}\n\n',
        'data: {"tool":{"name":"get_me","state":"running"}}\n\n',
        'data: {"error":"Sign in again.","code":"session_expired"}\n\n',
      ])
    )
    const got: unknown[] = []
    const streaming = streamEvents(
      "/assistant/chat",
      { message: "Hi" },
      (event) => got.push(event),
      new AbortController().signal
    )

    await expect(streaming).rejects.toBeInstanceOf(StreamError)
    await expect(streaming).rejects.toMatchObject({
      message: "Sign in again.",
      code: "session_expired",
    })
    expect(got).toEqual([
      { conversation: { id: "c1" } },
      { tool: { name: "get_me", state: "running" } },
    ])
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe("/api/assistant/chat")
  })
})
