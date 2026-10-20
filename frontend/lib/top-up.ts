import type { Catalog } from "@/types/billing"

type Custom = Catalog["custom"]

// Each price's area on the top-up slider has this many steps, whatever its size, so the
// areas are as wide as each other.
export const AREA_STEPS = 1000

/** The candidates in each price's area of the slider: from its first count to the next's
 * (the last one's to the maximum, which ends the track). */
function spans(custom: Custom) {
  return custom.tiers.map((tier, index) => {
    const next = custom.tiers[index + 1]

    return {
      from: tier.from_candidates,
      span:
        (next ? next.from_candidates : custom.max_candidates) -
        tier.from_candidates,
    }
  })
}

/** The candidates at a point of the slider, counted evenly within its price's area. */
export function candidatesAt(custom: Custom, position: number) {
  const areas = spans(custom)
  const index = Math.min(
    Math.max(Math.floor(position / AREA_STEPS), 0),
    areas.length - 1
  )
  const { from, span } = areas[index]
  const count =
    from + Math.round(((position - index * AREA_STEPS) / AREA_STEPS) * span)

  return Math.min(Math.max(count, custom.min_candidates), custom.max_candidates)
}

/** Where on the slider a number of candidates sits. */
export function positionOf(custom: Custom, candidates: number) {
  const areas = spans(custom)
  const index = areas.findLastIndex((area) => candidates >= area.from)

  return (
    (index + (candidates - areas[index].from) / areas[index].span) * AREA_STEPS
  )
}

/** What billing sells for a chosen number of candidates, as its catalog says: the count at
 * its tier's price, or the next tier's smallest top-up from the count billing gives for it;
 * on sale once billing's Paddle product for it is set. */
export function customTopUp(custom: Custom, candidates: number) {
  const index = custom.tiers.findLastIndex(
    (tier) => candidates >= tier.from_candidates
  )
  const tier = custom.tiers[index]
  const upgrade = tier.upgrade_from !== null && candidates >= tier.upgrade_from
  const bought = upgrade ? custom.tiers[index + 1] : tier
  const count = upgrade ? bought.from_candidates : candidates

  return {
    candidates: count,
    cents: count * bought.cents,
    onSale: custom.on_sale,
    upgraded: upgrade,
  }
}
