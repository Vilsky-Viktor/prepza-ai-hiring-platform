"use client"

import { Wire } from "@/components/landing/wire"
import {
  HERO_WIRES,
  OUT_SIZE,
  OUT_THICKNESS,
  OUT_SPEED,
  WIRE_GAP,
  WIRE_UNIT,
} from "@/config/landing"
import { useElementSize } from "@/hooks/use-element-size"

/** Wires around the job description box, in the focused box's border colour: on the left, from
 * the window's edge, each with a candidate's icon running along it into the box; on the right,
 * one straight wire out of the box to the window's edge, its candidates bigger and slower. Drawn
 * from tablets up, where the box doesn't span the screen; without motion, the wires alone.
 * Decoration only. */
export function HeroWires() {
  return (
    <>
      <Side wires={HERO_WIRES} />
      <Out />
    </>
  )
}

/** The right side's straight wire, from the box's middle out to the page's edge (the page's
 * container, app/page.tsx: never over a scrollbar's gutter, so the page can't scroll sideways). */
function Out() {
  const { ref, size } = useElementSize<SVGSVGElement>()

  return (
    <svg
      ref={ref}
      aria-hidden
      className="pointer-events-none absolute inset-y-0 left-full hidden h-full w-[calc((100cqw-100%)/2)] overflow-visible text-ring sm:block"
    >
      {size && (
        <Wire
          d={`M 0 ${size.height / 2} L ${size.width} ${size.height / 2}`}
          traveller="candidate"
          size={OUT_SIZE}
          thickness={OUT_THICKNESS}
          speed={OUT_SPEED}
        />
      )}
    </svg>
  )
}

/** The left side's wires, in a box from the window's edge to the job description box. Its curves are
 * drawn in pixels once its size is known, so a spark is one short piece at any width. */
function Side({ wires }: { wires: typeof HERO_WIRES }) {
  const { ref, size } = useElementSize<SVGSVGElement>()

  return (
    <svg
      ref={ref}
      aria-hidden
      className="pointer-events-none absolute inset-y-0 right-full hidden h-full w-[calc((100cqw-100%)/2)] overflow-visible text-ring sm:block"
    >
      {size &&
        wires.map((wire) => {
          const x = (percent: number) => (percent * size.width) / 100
          const y = (unit: number) => size.height / 2 + (unit - 50) * WIRE_UNIT
          const [[x1, y1], [x2, y2]] = wire.bends
          const path = `M 0 ${y(wire.from)} C ${x(x1)} ${y(y1)}, ${x(x2)} ${y(y2)}, ${size.width} ${size.height / 2 + wire.to * WIRE_GAP}`

          return (
            <Wire
              key={wire.from}
              d={path}
              delay={wire.delay}
              traveller="candidate"
            />
          )
        })}
    </svg>
  )
}
