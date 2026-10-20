import { describe, expect, it } from "vitest"

import { AREA_STEPS, candidatesAt, customTopUp, positionOf } from "@/lib/top-up"
import type { Catalog } from "@/types/billing"

// Billing's catalog: four levels, the next one bought instead from `upgrade_from`.
const custom: Catalog["custom"] = {
  min_candidates: 10,
  max_candidates: 1000,
  on_sale: true,
  tiers: [
    { from_candidates: 10, cents: 500, upgrade_from: 40 },
    { from_candidates: 50, cents: 400, upgrade_from: 150 },
    { from_candidates: 200, cents: 300, upgrade_from: 334 },
    { from_candidates: 500, cents: 200, upgrade_from: null },
  ],
}

describe("the slider", () => {
  it("gives each level an equal part of the track", () => {
    expect(positionOf(custom, 10)).toBe(0)
    expect(positionOf(custom, 50)).toBe(AREA_STEPS)
    expect(positionOf(custom, 200)).toBe(2 * AREA_STEPS)
    expect(positionOf(custom, 500)).toBe(3 * AREA_STEPS)
    expect(positionOf(custom, 1000)).toBe(4 * AREA_STEPS)
  })

  it("counts evenly within a level and keeps to the range", () => {
    expect(candidatesAt(custom, AREA_STEPS / 2)).toBe(30)
    expect(candidatesAt(custom, 2.5 * AREA_STEPS)).toBe(350)
    expect(candidatesAt(custom, -5)).toBe(10)
    expect(candidatesAt(custom, 4 * AREA_STEPS)).toBe(1000)
  })

  it("lands on the count it shows", () => {
    for (const count of [10, 39, 49, 50, 149, 199, 333, 499, 500, 777, 1000]) {
      expect(candidatesAt(custom, positionOf(custom, count))).toBe(count)
    }
  })
})

describe("what a count buys", () => {
  it.each([
    [39, 39, 19_500, false],
    [40, 50, 20_000, true],
    [149, 149, 59_600, false],
    [150, 200, 60_000, true],
    [333, 333, 99_900, false],
    [334, 500, 100_000, true],
    [1000, 1000, 200_000, false],
  ])(
    "%i candidates buy %i for %i cents",
    (chosen, candidates, cents, upgraded) => {
      expect(customTopUp(custom, chosen)).toMatchObject({
        candidates,
        cents,
        upgraded,
      })
    }
  )

  it("is on sale once billing's catalog says so", () => {
    expect(customTopUp(custom, 160).onSale).toBe(true)
    expect(customTopUp({ ...custom, on_sale: false }, 160).onSale).toBe(false)
  })
})
