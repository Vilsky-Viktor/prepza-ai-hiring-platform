import { useId } from "react"

import type { Area } from "@/lib/section-area"

// How far past the ellipse's edge the grey net fades out, as a share of the stage's width: out
// towards the window's edges and the section's top and bottom.
const FADE = 0.8

/** The quality loop's net continued outside its ellipse, for its SVG: the same mesh (`cell`
 * pixels, turned 45°, on the same origin, so its lines run on across the edge) in the borders'
 * grey, fading out with distance from the ellipse (`cx`, `cy`, `rx`, `ry`); `width` is the
 * stage's. It stays within `area` (its section, across the page), and inside the ellipse it
 * draws nothing, leaving the blue net as it is. */
export function NetOutside({
  cx,
  cy,
  rx,
  ry,
  width,
  area,
  cell,
}: {
  cx: number
  cy: number
  rx: number
  ry: number
  width: number
  area: Area
  cell: number
}) {
  // Ids for url(), letters and digits only.
  const id = useId().replace(/[^a-zA-Z0-9]/g, "")
  const mesh = `outside-net-${id}`
  const fade = `outside-fade-${id}`
  const shown = `outside-mask-${id}`
  // The fade's reach along the long axis; across, it keeps the ellipse's shape.
  const reach = rx + FADE * width
  const box = area

  return (
    <g aria-hidden>
      <defs>
        <pattern
          id={mesh}
          width={cell}
          height={cell}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <path
            d={`M 0 0 H ${cell} M 0 0 V ${cell}`}
            fill="none"
            strokeWidth={1}
            className="stroke-border"
          />
        </pattern>
        <radialGradient
          id={fade}
          gradientUnits="userSpaceOnUse"
          cx={cx}
          cy={cy}
          r={reach}
          gradientTransform={`translate(${cx} ${cy}) scale(1 ${ry / rx}) translate(${-cx} ${-cy})`}
        >
          {/* A long, slow fade: half gone a third of the way out. */}
          <stop offset={rx / reach} stopColor="white" />
          <stop
            offset={rx / reach + (1 - rx / reach) / 3}
            stopColor="white"
            stopOpacity={0.5}
          />
          <stop offset={1} stopColor="white" stopOpacity={0} />
        </radialGradient>
        {/* Shown outside the ellipse only, fading with distance from its edge. */}
        <mask id={shown} maskUnits="userSpaceOnUse" {...box}>
          <rect {...box} fill={`url(#${fade})`} />
          <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="black" />
        </mask>
      </defs>
      <rect {...box} fill={`url(#${mesh})`} mask={`url(#${shown})`} />
    </g>
  )
}
