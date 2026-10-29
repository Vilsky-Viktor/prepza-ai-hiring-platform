import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  clearChat,
  newer,
  readChat,
  recentVisitorChat,
  saveChat,
  wasOpen,
} from "@/lib/assistant-storage"

/** A Storage kept in a map. */
function memory() {
  const items = new Map<string, string>()

  return {
    getItem: (name: string) => items.get(name) ?? null,
    setItem: (name: string, value: string) => void items.set(name, value),
    removeItem: (name: string) => void items.delete(name),
  }
}

beforeEach(() => {
  vi.stubGlobal("localStorage", memory())
  vi.stubGlobal("sessionStorage", memory())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("the saved chat", () => {
  it("keeps the signed-in conversation and the visitor's messages apart", () => {
    saveChat(true, { open: true, choice: { page: null, company: "c1" } })
    saveChat(false, {
      messages: [{ role: "user", content: "Hi", blocks: [] }],
    })

    expect(readChat(true)).toEqual({
      open: true,
      choice: { page: null, company: "c1" },
    })
    expect(readChat(false).messages).toHaveLength(1)
    expect(localStorage.getItem("prepza:assistant:visitor")).toBeNull()
  })

  it("adds a change to what's saved", () => {
    saveChat(true, { open: true, choice: { page: null, company: "c1" } })
    saveChat(true, { open: false })

    expect(readChat(true)).toEqual({
      open: false,
      choice: { page: null, company: "c1" },
    })
  })

  it("reads nothing from a broken or blocked store", () => {
    localStorage.setItem("prepza:assistant", "{broken")
    expect(readChat(true)).toEqual({})

    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("blocked")
      },
      setItem: () => {
        throw new Error("blocked")
      },
    })
    expect(readChat(true)).toEqual({})
    expect(() => saveChat(true, { open: true })).not.toThrow()
  })

  it("reopens for the visitor who was signing in, and signing out forgets both", () => {
    saveChat(false, { open: true })
    expect(wasOpen(true)).toBe(true)
    expect(wasOpen(false)).toBe(true)

    saveChat(true, { open: true, choice: { page: null, company: "c1" } })
    clearChat(true)
    expect(readChat(true)).toEqual({})
    expect(readChat(false)).toEqual({})
    expect(wasOpen(true)).toBe(false)
  })

  it("forgets only the visitor's chat once it's part of a saved conversation", () => {
    saveChat(true, { choice: { page: null, company: "c1" } })
    saveChat(false, { open: true })
    clearChat(false)

    expect(readChat(true)).toEqual({ choice: { page: null, company: "c1" } })
    expect(readChat(false)).toEqual({})
  })
})

describe("a visitor's chat after a reload", () => {
  const config = {
    max_message_length: 2000,
    restore_minutes: 30,
    max_audio_seconds: 60,
    messages_per_hour: 30,
    messages_per_day: 200,
  }
  const messages = [{ role: "user" as const, content: "Hi", blocks: [] }]
  const now = Date.parse("2026-10-09T12:00:00Z")

  it("comes back within the service's window, up to its last moment", () => {
    const lastAt = "2026-10-09T11:31:00Z"

    expect(recentVisitorChat({ messages, lastAt }, config, now)).toEqual(
      messages
    )
    expect(
      recentVisitorChat(
        { messages, lastAt: "2026-10-09T11:30:00Z" },
        config,
        now
      )
    ).toEqual(messages)
  })

  it("doesn't when it's older, has no time, or the window is unknown", () => {
    const old = { messages, lastAt: "2026-10-09T11:29:00Z" }
    const justPast = { messages, lastAt: "2026-10-09T11:29:59.999Z" }

    expect(recentVisitorChat(old, config, now)).toBeNull()
    expect(recentVisitorChat(justPast, config, now)).toBeNull()
    expect(
      recentVisitorChat(
        { messages: [], lastAt: "2026-10-09T11:59:00Z" },
        config,
        now
      )
    ).toBeNull()
    expect(recentVisitorChat({ messages }, config, now)).toBeNull()
    expect(
      recentVisitorChat({ messages, lastAt: "2026-10-09T11:59:00Z" }, null, now)
    ).toBeNull()
    expect(
      recentVisitorChat({ lastAt: "2026-10-09T11:59:00Z" }, config, now)
    ).toBeNull()
  })
})

describe("newer", () => {
  it("says whether a saved conversation came after the visitor's last message", () => {
    expect(newer("2026-10-09T12:05:00Z", "2026-10-09T12:00:00Z")).toBe(true)
    expect(newer("2026-10-09T11:55:00Z", "2026-10-09T12:00:00Z")).toBe(false)
    expect(newer(null, "2026-10-09T12:00:00Z")).toBe(false)
  })
})
