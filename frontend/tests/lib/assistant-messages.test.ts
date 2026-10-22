import { describe, expect, it } from "vitest"

import { shownMessage } from "@/lib/assistant"
import type { AssistantMessage } from "@/types/assistant"

describe("shownMessage", () => {
  it("keeps what the panel shows of a stored message", () => {
    const stored = {
      id: "m1",
      role: "assistant",
      source: "text",
      content: "**Ann** passed.",
      blocks: [],
      status: "complete",
      vote: 1,
      created_at: "2026-10-09T10:00:00Z",
    } as unknown as AssistantMessage

    expect(shownMessage(stored)).toEqual({
      role: "assistant",
      content: "**Ann** passed.",
      blocks: [],
      source: "text",
      id: "m1",
      vote: 1,
    })
  })
})
