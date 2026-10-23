// The comet's trail: how many fading copies follow it, and how far apart along the wire, in pixels.
const TRAIL = 4
const TRAIL_GAP = 4

/** A wire's traveller as a small glowing dot in the primary colour with a short fading trail,
 * for an SVG: `animations` move and fade the dot itself (the main motion's id is `motion`); each
 * trailing copy runs the same `path` for `seconds`, starting a few pixels' time behind it at
 * `speed` pixels a second, once or `repeat`ing as the dot does. */
export function Comet({
  animations,
  motion,
  path,
  seconds,
  speed,
  repeat,
}: {
  animations: React.ReactNode
  motion: string
  path: string
  seconds: number
  speed: number
  repeat?: string
}) {
  return (
    <g className="motion-reduce:hidden">
      {Array.from({ length: TRAIL }, (_, at) => {
        const behind = at + 1
        const begin = `${motion}.begin+${(behind * TRAIL_GAP) / speed}s`
        const peak = 0.5 * (1 - at / TRAIL)

        return (
          <circle
            key={at}
            r={3.5 - at * 0.6}
            opacity={0}
            className="fill-primary"
          >
            <animateMotion
              path={path}
              dur={`${seconds}s`}
              begin={begin}
              repeatCount={repeat}
            />
            <animate
              attributeName="opacity"
              values={`0;${peak};${peak};0`}
              keyTimes="0;0.2;0.8;1"
              dur={`${seconds}s`}
              begin={begin}
              repeatCount={repeat}
            />
          </circle>
        )
      })}
      <g opacity={0} data-testid="wire-traveller">
        {animations}
        {/* The halo, then the dot. */}
        <circle r={10} opacity={0.3} className="fill-primary blur-[3px]" />
        <circle r={4} className="fill-primary" />
      </g>
    </g>
  )
}
