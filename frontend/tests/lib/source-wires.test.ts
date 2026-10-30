import { describe, expect, it } from "vitest"

import { reversed, sourceWires } from "@/lib/source-wires"

const numbers = (d: string) => d.match(/-?[\d.]+/g)!.map(Number)
// Where a wire starts and where it ends.
const ends = (d: string) => {
  const all = numbers(d)

  return { from: all.slice(0, 2), to: all.slice(6, 8) }
}

// A card in the middle of the frame: 100 to 200 across, 100 to 160 down.
const CARD = { left: 100, top: 100, width: 100, height: 60 }

describe("sourceWires", () => {
  it("meets the near side of a card beside it, from inside the source's facing side", () => {
    const left = { left: 0, top: 110, width: 40, height: 40 }
    const right = { left: 260, top: 110, width: 40, height: 40 }
    const [fromLeft, fromRight] = sourceWires(CARD, [left, right], 10, 4)

    expect(ends(fromLeft)).toEqual({ from: [36, 130], to: [100, 130] })
    expect(ends(fromRight)).toEqual({ from: [264, 130], to: [200, 130] })
  })

  it("meets the top or bottom of a card above or below it", () => {
    const above = { left: 130, top: 0, width: 40, height: 40 }
    const below = { left: 130, top: 220, width: 40, height: 40 }
    const [fromAbove, fromBelow] = sourceWires(CARD, [above, below], 10, 4)

    expect(ends(fromAbove)).toEqual({ from: [150, 36], to: [150, 100] })
    expect(ends(fromBelow)).toEqual({ from: [150, 224], to: [150, 160] })
  })

  it("spaces wires on one side by the gap, in the sources' order, around the middle", () => {
    const top = { left: 0, top: 0, width: 40, height: 40 }
    const middle = { left: 0, top: 110, width: 40, height: 40 }
    const bottom = { left: 0, top: 220, width: 40, height: 40 }
    // Given out of order, they still meet the card in order, so no two cross.
    const wires = sourceWires(CARD, [bottom, top, middle], 12, 0)

    expect(wires.map((wire) => ends(wire).to[1])).toEqual([142, 118, 130])
  })

  it("leaves and meets straight on", () => {
    const [wire] = sourceWires(
      CARD,
      [{ left: 0, top: 0, width: 40, height: 40 }],
      10,
      0
    )
    const [x1, y1, ax, ay, bx, by, x2, y2] = numbers(wire)

    // Beside the card: level as it leaves the source and as it reaches the card.
    expect(ay).toBe(y1)
    expect(by).toBe(y2)
    expect(ax).toBe(bx)
    expect(x1).toBeLessThan(x2)
  })
})

describe("sourceWires' turning wires", () => {
  it("comes down near the card's side, then turns into it, for a source above and close to it", () => {
    // Above the card, 20 px off its left side.
    const [wire] = sourceWires(
      CARD,
      [{ left: 20, top: 0, width: 60, height: 40 }],
      10,
      4
    )

    // Down at 56 px off the side, then level into the side's middle.
    expect(wire).toBe("M 44 36 C 44 130, 44 130, 100 130")
  })

  it("turns from within the source when it reaches over the card's side", () => {
    // Above, reaching 30 px over the left side, its middle still left of the card.
    const [wire] = sourceWires(
      CARD,
      [{ left: 60, top: 0, width: 70, height: 40 }],
      10,
      4
    )

    expect(ends(wire)).toEqual({ from: [64, 36], to: [100, 130] })
    expect(numbers(wire)[2]).toBe(64)
  })

  it("comes up into the far side for a source below and close to it", () => {
    const [wire] = sourceWires(
      CARD,
      [{ left: 190, top: 200, width: 40, height: 40 }],
      10,
      4
    )

    expect(wire).toBe("M 226 204 C 226 130, 226 130, 200 130")
  })

  it("keeps its place among the other wires on that side", () => {
    const turning = { left: 20, top: 0, width: 60, height: 40 }
    const beside = { left: 0, top: 110, width: 40, height: 40 }
    const [fromTurning, fromBeside] = sourceWires(
      CARD,
      [turning, beside],
      10,
      0
    )

    // The higher source meets the side higher, so the two never cross.
    expect(ends(fromTurning).to).toEqual([100, 125])
    expect(ends(fromBeside).to).toEqual([100, 135])
  })

  it("runs straight for a source well off the side", () => {
    // 60 px off the left side: the plain curve, leaving level from the source's side.
    const [wire] = sourceWires(
      CARD,
      [{ left: 0, top: 0, width: 40, height: 40 }],
      10,
      4
    )

    expect(ends(wire).from).toEqual([36, 20])
  })
})

describe("reversed", () => {
  it("draws the same curve from its other end", () => {
    expect(reversed("M 1 2 C 3 4, 5 6, 7 8")).toBe("M 7 8 C 5 6, 3 4, 1 2")
  })

  it("keeps negative and fractional numbers", () => {
    expect(reversed("M -1.5 2 C 3 -4.25, 5 6, 7 8")).toBe(
      "M 7 8 C 5 6, 3 -4.25, -1.5 2"
    )
  })
})
