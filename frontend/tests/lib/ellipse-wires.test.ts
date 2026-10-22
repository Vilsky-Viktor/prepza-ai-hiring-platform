import { describe, expect, it } from "vitest"

import { ellipsePoints, ellipseWires } from "@/lib/ellipse-wires"

const numbers = (d: string) => d.match(/-?[\d.]+/g)!.map(Number)

describe("ellipsePoints", () => {
  it("starts at the top and spaces the points evenly round the ellipse", () => {
    const points = ellipsePoints(5, 36, 34)

    expect(points).toHaveLength(5)
    expect(points[0].x).toBeCloseTo(50)
    expect(points[0].y).toBeCloseTo(16)
    points.forEach(({ x, y }) => {
      expect(((x - 50) / 36) ** 2 + ((y - 50) / 34) ** 2).toBeCloseTo(1)
    })
  })

  it("mirrors left and right", () => {
    const [, right, lowerRight, lowerLeft, left] = ellipsePoints(5, 36, 34)

    expect(left.x).toBeCloseTo(100 - right.x)
    expect(left.y).toBeCloseTo(right.y)
    expect(lowerLeft.x).toBeCloseTo(100 - lowerRight.x)
    expect(lowerLeft.y).toBeCloseTo(lowerRight.y)
  })
})

describe("ellipseWires", () => {
  const centre = { x: 50, y: 50 }
  // Clockwise on screen: top, right, bottom, left.
  const points = [
    { x: 50, y: 10 },
    { x: 90, y: 50 },
    { x: 50, y: 90 },
    { x: 10, y: 50 },
  ]

  it("draws an arc of the ellipse from each point to the next, the last back to the first", () => {
    const wires = ellipseWires(points, centre, 40, 40)

    expect(wires).toHaveLength(4)
    wires.forEach((wire, index) => {
      const [x1, y1, rx, ry, , , , x2, y2] = numbers(wire)
      const to = points[(index + 1) % points.length]

      expect([x1, y1, rx, ry]).toEqual([
        points[index].x,
        points[index].y,
        40,
        40,
      ])
      expect([x2, y2]).toEqual([to.x, to.y])
    })
  })

  it("turns the way the points run round the centre", () => {
    const sweep = (wire: string) => numbers(wire)[6]

    expect(ellipseWires(points, centre, 40, 40).map(sweep)).toEqual([
      1, 1, 1, 1,
    ])
    expect(
      ellipseWires([...points].reverse(), centre, 40, 40).map(sweep)
    ).toEqual([0, 0, 0, 0])
  })
})
