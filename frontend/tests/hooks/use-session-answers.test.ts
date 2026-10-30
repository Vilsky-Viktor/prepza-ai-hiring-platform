import { describe, expect, it } from "vitest"

import { toggled } from "@/hooks/use-session-answers"

describe("toggled", () => {
  it("makes a tapped option the pick of a one-answer question", () => {
    expect(toggled([], 2, false)).toEqual([2])
    expect(toggled([2], 0, false)).toEqual([0])
    expect(toggled([2], 2, false)).toEqual([2])
  })

  it("ticks and unticks each option of a multi-answer question on its own", () => {
    expect(toggled([], 1, true)).toEqual([1])
    expect(toggled([1], 3, true)).toEqual([1, 3])
    expect(toggled([1, 3], 1, true)).toEqual([3])
  })
})
