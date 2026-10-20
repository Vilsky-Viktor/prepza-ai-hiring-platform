import type { KeyboardEvent } from "react"
import { describe, expect, it } from "vitest"

import { isChatNewLine, isChatSend, isSubmitShortcut } from "@/lib/keys"

/** An Enter press with these modifiers, typed or mid-composition (an IME). */
function enter({
  meta = false,
  ctrl = false,
  shift = false,
  composing = false,
} = {}) {
  return {
    key: "Enter",
    metaKey: meta,
    ctrlKey: ctrl,
    shiftKey: shift,
    nativeEvent: { isComposing: composing },
  } as unknown as KeyboardEvent
}

describe("chat keys", () => {
  it("sends on plain Enter only", () => {
    expect(isChatSend(enter())).toBe(true)
    expect(isChatSend(enter({ ctrl: true }))).toBe(false)
    expect(isChatSend(enter({ meta: true }))).toBe(false)
    expect(isChatSend(enter({ shift: true }))).toBe(false)
    expect(isChatSend(enter({ composing: true }))).toBe(false)
  })

  it("adds a new line on ⌘/Ctrl + Enter", () => {
    expect(isChatNewLine(enter({ ctrl: true }))).toBe(true)
    expect(isChatNewLine(enter({ meta: true }))).toBe(true)
    expect(isChatNewLine(enter())).toBe(false)
    expect(isChatNewLine(enter({ ctrl: true, composing: true }))).toBe(false)
  })

  it("leaves the other inputs sending on ⌘/Ctrl + Enter", () => {
    expect(isSubmitShortcut(enter({ ctrl: true }))).toBe(true)
    expect(isSubmitShortcut(enter())).toBe(false)
  })
})
