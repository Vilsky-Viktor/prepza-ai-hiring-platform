import { describe, expect, it } from "vitest"

import { gradeTone } from "@/lib/grade-tone"

describe("gradeTone", () => {
  it("is green for a pass and red for a fail", () => {
    expect(gradeTone(true)).toContain("text-green-700")
    expect(gradeTone(false)).toContain("text-red-700")
  })

  it("has no colour while the result isn't decided", () => {
    expect(gradeTone(null)).toBe("")
    expect(gradeTone(undefined)).toBe("")
  })
})
