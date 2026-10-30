export type Box = { left: number; top: number; width: number; height: number }

// How far from the card's side a source above or below it, beside it, comes down (or up), in
// pixels; a source standing off the side by less than this turns into it (turningWire).
const REACH_OFFSET = 56

/** The wires from each of `sources` to `card` (boxes in the same frame, in pixels), as SVG
 * curves: from `inset` pixels inside the source's side that faces the card to the card's edge,
 * leaving and meeting it straight on. A source beside the card (by its middle) meets its near
 * side, coming down or up into it when it also stands above or below the card close to its
 * side (turningWire); one above or below meets
 * its top or bottom; the wires meeting one side are `gap` pixels apart there, in
 * the sources' order along it, so they never cross. */
export function sourceWires(
  card: Box,
  sources: Box[],
  gap: number,
  inset: number
) {
  // By the source's middle: one mostly beside the card meets its side, even when its edge
  // reaches over the card (a wide card above and to the side).
  const sideOf = (box: Box) => {
    const middle = box.left + box.width / 2

    if (middle < card.left) {
      return "left"
    }

    if (middle > card.left + card.width) {
      return "right"
    }

    return box.top + box.height <= card.top ? "top" : "bottom"
  }
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
      const turning = turningWire(card, box, side, step, inset)

      if (turning) {
        return turning
      }
    }

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

/** The wire of a source beside the card (on `side`) that also stands above or below it and
 * reaches over the card's side or comes close to it: down (or up) near the card's side, then
 * round into it, so it passes inside the other wires on that side, never across. Null for any
 * other source. */
function turningWire(
  card: Box,
  box: Box,
  side: "left" | "right",
  step: number,
  inset: number
) {
  const right = card.left + card.width
  // How far the source stands off the card's side (negative when it reaches over it).
  const offSide =
    side === "left" ? card.left - (box.left + box.width) : box.left - right
  const above = box.top + box.height <= card.top
  const below = box.top >= card.top + card.height

  if (!(above || below) || offSide >= REACH_OFFSET) {
    return null
  }

  const x2 = side === "left" ? card.left : right
  const y2 = card.top + card.height / 2 + step
  const near = side === "left" ? card.left - REACH_OFFSET : right + REACH_OFFSET
  const x1 = Math.min(
    Math.max(near, box.left + inset),
    box.left + box.width - inset
  )
  const y1 = above ? box.top + box.height - inset : box.top + inset

  return `M ${x1} ${y1} C ${x1} ${y2}, ${x1} ${y2}, ${x2} ${y2}`
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
