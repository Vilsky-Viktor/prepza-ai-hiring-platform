import { describe, expect, it } from "vitest"

import {
  countedAt,
  pointedAt,
  seenOnScreen,
  skips,
  stepIndex,
} from "@/hooks/use-demo-steps"

const SCREEN = 800

function entry(visibleHeight: number, height: number) {
  return {
    isIntersecting: visibleHeight > 0,
    intersectionRatio: visibleHeight / height,
    intersectionRect: { height: visibleHeight } as DOMRectReadOnly,
  }
}

describe("seenOnScreen", () => {
  it("counts a short demo as seen once enough of it is on screen", () => {
    expect(seenOnScreen(entry(100, 400), SCREEN)).toBe(false)
    expect(seenOnScreen(entry(200, 400), SCREEN)).toBe(true)
  })

  it("counts a demo taller than the screen as seen by its share of the screen", () => {
    // A 3,000 px stack of panels never shows 40% of itself on an 800 px screen.
    expect(seenOnScreen(entry(400, 3000), SCREEN)).toBe(true)
    expect(seenOnScreen(entry(200, 3000), SCREEN)).toBe(false)
  })

  it("keeps a tall demo seen while scrolling within it", () => {
    const scrolled = [800, 700, 500, 400].map((visible) =>
      seenOnScreen(entry(visible, 3000), SCREEN)
    )

    expect(scrolled).toEqual([true, true, true, true])
  })

  it("never counts a demo off screen", () => {
    expect(seenOnScreen(entry(0, 400), SCREEN)).toBe(false)
  })
})

describe("skips", () => {
  it("moves a playing demo on to a later step only", () => {
    expect(skips(true, 2, 5)).toBe(true)
    expect(skips(true, 5, 5)).toBe(false)
    expect(skips(true, 6, 5)).toBe(false)
  })

  it("leaves a demo that isn't playing where it is", () => {
    expect(skips(false, 2, 5)).toBe(false)
  })
})

// A demo's steps: a pause, a pointer moved, five letters typed, the pointer hidden.
const STEPS = [
  { name: "start", ms: 100 },
  { name: "aim", ms: 100, point: "field" },
  { name: "typing", ms: 50, repeat: 5 },
  { name: "done", ms: 100, point: "none" },
]

describe("stepIndex", () => {
  it("finds a step by its name", () => {
    expect(stepIndex(STEPS, "typing")).toBe(2)
    expect(stepIndex(STEPS, "missing")).toBe(-1)
  })
})

describe("countedAt", () => {
  it("counts nothing before the step, its count during it and all of it after", () => {
    expect(countedAt(STEPS, { index: 1, n: 0 }, "typing", 5)).toBe(0)
    expect(countedAt(STEPS, { index: 2, n: 3 }, "typing", 5)).toBe(3)
    expect(countedAt(STEPS, { index: 3, n: 0 }, "typing", 5)).toBe(5)
  })
})

describe("pointedAt", () => {
  it("is the last target a step so far moved the pointer to", () => {
    expect(pointedAt(STEPS, 0)).toBeUndefined()
    expect(pointedAt(STEPS, 2)).toBe("field")
    expect(pointedAt(STEPS, 3)).toBe("none")
  })
})
