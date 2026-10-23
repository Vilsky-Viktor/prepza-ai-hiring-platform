import { describe, expect, it } from "vitest"

import { adornmentRoom, alwaysFilled } from "@/lib/floating-field"

describe("floating field labels", () => {
  it("keeps the label raised on fields that always show something", () => {
    for (const type of ["date", "time", "datetime-local", "month", "week"]) {
      expect(alwaysFilled(type)).toBe(true)
    }

    for (const type of [
      undefined,
      "text",
      "email",
      "number",
      "password",
      "search",
    ]) {
      expect(alwaysFilled(type)).toBe(false)
    }
  })

  it("keeps room for a sign or unit by its length, and none without one", () => {
    expect(adornmentRoom(undefined)).toBeUndefined()
    expect(adornmentRoom("")).toBeUndefined()
    expect(adornmentRoom("px")).toBe("calc(2rem + 2ch)")
    expect(adornmentRoom("credits")).toBe("calc(2rem + 7ch)")
    // Counted as people see it: a currency sign with a mark is one.
    expect(adornmentRoom("₹")).toBe("calc(2rem + 1ch)")
    expect(adornmentRoom("👩‍💻")).toBe("calc(2rem + 1ch)")
  })
})
