import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { voteAnswer, withEvent } from "@/lib/assistant"
import type { ChatMessage } from "@/types/assistant"

// No Firebase in a unit test: nobody is signed in.
vi.mock("@/lib/firebase", () => ({
  firebaseAuth: async () => ({
    authStateReady: async () => {},
    currentUser: null,
  }),
}))

const HELP_ANSWER = {
  id: "c87785d7-1ace-4a4c-9e4b-7c9b93a6387a",
  trace_id: "15e22744a64a4538a7da68ffb20c114a",
  signature: "5f70",
}

function writing(): ChatMessage {
  return { role: "assistant", content: "", blocks: [] }
}

describe("withEvent", () => {
  it("builds the answer from its events", () => {
    let answer = writing()

    for (const event of [
      { tool: { name: "t", state: "running" as const, label: "Reading…" } },
      { tool: { name: "t", state: "done" as const, label: "Reading…" } },
      { delta: "Ann " },
      { delta: "passed." },
    ]) {
      answer = withEvent(answer, event)
    }

    expect(answer).toEqual({
      role: "assistant",
      content: "Ann passed.",
      blocks: [],
      progress: ["Reading…"],
    })
  })

  it("keeps the assistant's saved answer id for a vote", () => {
    const answer = withEvent(writing(), { done: { message_id: "m1" } })

    expect(answer.id).toBe("m1")
    expect(answer.helpAnswer).toBeUndefined()
  })

  it("keeps the help chat's signature and answer for a vote", () => {
    const answer = withEvent(writing(), {
      done: true,
      signature: "abc",
      answer: HELP_ANSWER,
    })

    expect(answer).toMatchObject({ signature: "abc", helpAnswer: HELP_ANSWER })
    expect(answer.id).toBeUndefined()
  })
})

describe("voteAnswer", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    vi.stubGlobal("document", { documentElement: { lang: "en" } })
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 204 }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("puts a vote on the assistant's answer in its conversation", async () => {
    await voteAnswer("conv-1", { ...writing(), id: "m1" }, 1)

    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe("/api/assistant/conversations/conv-1/messages/m1/vote")
    expect(init?.method).toBe("PUT")
    expect(JSON.parse(String(init?.body))).toEqual({ value: 1 })
  })

  it("puts a help chat vote with the answer's run and signature, null to clear", async () => {
    await voteAnswer(null, { ...writing(), helpAnswer: HELP_ANSWER }, null)

    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe(`/api/assistant/help/answers/${HELP_ANSWER.id}/vote`)
    expect(JSON.parse(String(init?.body))).toEqual({
      trace_id: HELP_ANSWER.trace_id,
      signature: HELP_ANSWER.signature,
      value: null,
    })
  })
})
