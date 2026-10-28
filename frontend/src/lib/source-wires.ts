export type Box = { left: number; top: number; width: number; height: number }

/** The wires from each of `sources` to `card` (boxes in the same frame, in pixels), as SVG
 * curves: from `inset` pixels inside the source's side that faces the card to the card's edge,
 * leaving and meeting it straight on. A source beside the card meets its near side, one above
 * or below meets its top or bottom; the wires meeting one side are `gap` pixels apart there, in
 * the sources' order along it, so they never cross. */
export function sourceWires(
  card: Box,
  sources: Box[],
  gap: number,
  inset: number
) {
  const sideOf = (box: Box) =>
    box.left + box.width <= card.left
      ? "left"
      : box.left >= card.left + card.width
        ? "right"
        : box.top + box.height <= card.top
          ? "top"
          : "bottom"
  const across = (box: Box) =>
    ["left", "right"].includes(sideOf(box))
      ? box.top + box.height / 2
      : box.left + box.width / 2

  return sources.map((box) => {
    const side = sideOf(box)
    // Where it meets the card: its place among the sources on that side, around the middle.
    const sharing = sources
      .filter((other) => sideOf(other) === side)
      .sort((a, b) => across(a) - across(b))
    const step = (sharing.indexOf(box) - (sharing.length - 1) / 2) * gap

    if (side === "left" || side === "right") {
      const x1 =
        side === "left" ? box.left + box.width - inset : box.left + inset
      const y1 = box.top + box.height / 2
      const x2 = side === "left" ? card.left : card.left + card.width
      const y2 = card.top + card.height / 2 + step
      const middle = (x1 + x2) / 2

      return `M ${x1} ${y1} C ${middle} ${y1}, ${middle} ${y2}, ${x2} ${y2}`
    }

    const x1 = box.left + box.width / 2
    const y1 = side === "top" ? box.top + box.height - inset : box.top + inset
    const x2 = card.left + card.width / 2 + step
    const y2 = side === "top" ? card.top : card.top + card.height
    const middle = (y1 + y2) / 2

    return `M ${x1} ${y1} C ${x1} ${middle}, ${x2} ${middle}, ${x2} ${y2}`
  })
}

/** Where `element` is laid out in its positioned parent, as a box. */
export function boxOf(element: HTMLElement): Box {
  return {
    left: element.offsetLeft,
    top: element.offsetTop,
    width: element.offsetWidth,
    height: element.offsetHeight,
  }
}

/** One of `sourceWires`' curves the other way round, from the card to the source. */
export function reversed(d: string) {
  const [x1, y1, ax, ay, bx, by, x2, y2] = d.match(/-?[\d.]+(?:e-?\d+)?/g) ?? []

  return `M ${x2} ${y2} C ${bx} ${by}, ${ax} ${ay}, ${x1} ${y1}`
}
