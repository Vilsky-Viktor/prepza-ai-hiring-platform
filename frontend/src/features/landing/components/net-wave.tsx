"use client"

import { useId } from "react"

import { NET_WAVE_SECONDS, NET_WAVES } from "@/config/trust-quality-demo"

// A ring's width and its blur's deviation, in pixels, and the room its glow takes beyond the
// net's edge: half its width and three deviations.
const RING_WIDTH = 44
const BLUR = 24
const BLUR_ROOM = RING_WIDTH / 2 + 3 * BLUR

/** Light running through the quality loop's net, for its SVG: soft rings that spread from the
 * centre (`cx`, `cy`, from the chip's edge, `from` pixels out) to the ellipse's edge (`rx`, `ry`),
 * brightening only the net's lines as they pass, a few at a time. `cell` is the net's cell, in
 * pixels. Shown only while `playing`; SMIL animations ignore reduced motion, so the caller leaves
 * it out when the page should be still. */
export function NetWave({
  cx,
  cy,
  rx,
  ry,
  from,
  cell,
}: {
  cx: number
  cy: number
  rx: number
  ry: number
  from: number
  cell: number
}) {
  // Ids for url(), letters and digits only.
  const id = useId().replace(/[^a-zA-Z0-9]/g, "")
  const bright = `wave-net-${id}`
  const soft = `wave-soft-${id}`
  const rings = `wave-mask-${id}`
  const to = rx

  return (
    <g data-testid="net-wave" aria-hidden>
      <defs>
        {/* The same net as the loop's, its lines brighter. */}
        <pattern
          id={bright}
          width={cell}
          height={cell}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <path
            d={`M 0 0 H ${cell} M 0 0 V ${cell}`}
            fill="none"
            strokeWidth={1.25}
            className="stroke-primary"
          />
        </pattern>
        {/* The blur may draw over the whole net and round it: the usual 10% round each ring
            cut its glow off square, so the light ran out as a rectangle, not an oval. */}
        <filter
          id={soft}
          filterUnits="userSpaceOnUse"
          x={cx - rx - BLUR_ROOM}
          y={cy - ry - BLUR_ROOM}
          width={2 * (rx + BLUR_ROOM)}
          height={2 * (ry + BLUR_ROOM)}
        >
          <feGaussianBlur stdDeviation={BLUR} />
        </filter>
        {/* The rings: soft white bands growing from the chip to the edge, fading near it. */}
        <mask id={rings} maskUnits="userSpaceOnUse">
          {Array.from({ length: NET_WAVES }, (_, at) => {
            const begin = `${(at * NET_WAVE_SECONDS) / NET_WAVES}s`

            return (
              <ellipse
                key={at}
                cx={cx}
                cy={cy}
                fill="none"
                stroke="white"
                strokeWidth={RING_WIDTH}
                filter={`url(#${soft})`}
                opacity={0}
              >
                <animate
                  attributeName="rx"
                  values={`${from};${to}`}
                  dur={`${NET_WAVE_SECONDS}s`}
                  begin={begin}
                  repeatCount="indefinite"
                  calcMode="spline"
                  keyTimes="0;1"
                  keySplines="0.25 0.1 0.25 1"
                />
                <animate
                  attributeName="ry"
                  values={`${(from * ry) / rx};${(to * ry) / rx}`}
                  dur={`${NET_WAVE_SECONDS}s`}
                  begin={begin}
                  repeatCount="indefinite"
                  calcMode="spline"
                  keyTimes="0;1"
                  keySplines="0.25 0.1 0.25 1"
                />
                <animate
                  attributeName="opacity"
                  values="0;0.7;0.45;0"
                  keyTimes="0;0.25;0.7;1"
                  calcMode="spline"
                  keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"
                  dur={`${NET_WAVE_SECONDS}s`}
                  begin={begin}
                  repeatCount="indefinite"
                />
              </ellipse>
            )
          })}
        </mask>
      </defs>
      <ellipse
        cx={cx}
        cy={cy}
        rx={rx}
        ry={ry}
        fill={`url(#${bright})`}
        mask={`url(#${rings})`}
      />
    </g>
  )
}
