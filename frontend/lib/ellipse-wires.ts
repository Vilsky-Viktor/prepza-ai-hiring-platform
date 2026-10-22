type Point = { x: number; y: number }

/** `count` points spaced evenly round an ellipse centred on (50, 50) with radii `rx` and `ry`,
 * in the same units (percent of a box): the first at the top, then clockwise, so left and right
 * mirror each other. */
export function ellipsePoints(count: number, rx: number, ry: number) {
  return Array.from({ length: count }, (_, index) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * index) / count

    return { x: 50 + rx * Math.cos(angle), y: 50 + ry * Math.sin(angle) }
  })
}

/** The wires of a closed loop through `points` lying on an ellipse centred on `centre` with
 * radii `rx` and `ry`: one SVG arc from each point to the next, the last back to the first,
 * together the ellipse itself. Each arc turns the way the points run round the centre. */
export function ellipseWires(
  points: Point[],
  centre: Point,
  rx: number,
  ry: number
) {
  return points.map((from, index) => {
    const to = points[(index + 1) % points.length]
    const turn =
      (from.x - centre.x) * (to.y - centre.y) -
      (from.y - centre.y) * (to.x - centre.x)

    return `M ${from.x} ${from.y} A ${rx} ${ry} 0 0 ${turn > 0 ? 1 : 0} ${to.x} ${to.y}`
  })
}
