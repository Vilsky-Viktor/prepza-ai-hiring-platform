import { describe, expect, it } from "vitest"

import { seenOnScreen, skips } from "@/hooks/use-demo-steps"

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
