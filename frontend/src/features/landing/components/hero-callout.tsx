import { type ReactNode, useId } from "react"

// The callout's line: flat just under the button, from TAIL px past its middle on the title's
// side, FLAT px past its middle on the other, then rising at 30° for RUN px across towards the
// page's start edge; it fades out at both ends. The label sits on the rising part, along it.
const TAIL = 45
const FLAT = 30
const RUN = 120
const RISE = Math.round(RUN * Math.tan(Math.PI / 6))
const WIDTH = TAIL + FLAT + RUN
const HEIGHT = RISE + 1

/** A button beside the hero's title with a line drawn out from under it, flat at first, then
 * rising at 30° towards the page's start edge, and what the button does written along the
 * rising part ("watch video"). From wide screens, where the buttons stand in the margin; on
 * narrower ones the button alone. Decoration: the button keeps its own name. */
export function HeroCallout({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  const fade = useId()

  return (
    <span className="relative inline-flex">
      {children}
      <span
        aria-hidden
        className="pointer-events-none absolute top-[calc(100%+0.25rem)] hidden -translate-y-full xl:block rtl:-scale-x-100"
        style={{
          insetInlineEnd: `calc(50% - ${TAIL}px)`,
          width: WIDTH,
          height: HEIGHT,
        }}
      >
        <svg
          width={WIDTH}
          height={HEIGHT}
          className="absolute inset-0 overflow-visible text-muted-foreground/50"
        >
          {/* Fading in over the rise's far part, full to the button, fading out along the tail. */}
          <defs>
            <linearGradient
              id={fade}
              gradientUnits="userSpaceOnUse"
              x1={0}
              x2={WIDTH}
              y1={0}
              y2={0}
            >
              <stop offset="0" stopColor="currentColor" stopOpacity={0} />
              <stop offset={RUN / 2 / WIDTH} stopColor="currentColor" />
              <stop offset={(WIDTH - TAIL) / WIDTH} stopColor="currentColor" />
              <stop offset="1" stopColor="currentColor" stopOpacity={0} />
            </linearGradient>
          </defs>
          <path
            d={`M ${WIDTH} ${HEIGHT - 0.5} L ${RUN} ${HEIGHT - 0.5} L 0 0.5`}
            fill="none"
            stroke={`url(#${fade})`}
            strokeWidth={1}
          />
        </svg>
        {/* Its bottom middle on the rising part's middle, turned to run along it. */}
        <span
          // Placed as drawn (left to right); the whole callout is mirrored in right-to-left pages.
          dir="ltr"
          className="absolute mb-1 text-sm whitespace-nowrap text-muted-foreground/60 lowercase rtl:-scale-x-100"
          style={{
            insetInlineStart: RUN / 2,
            top: HEIGHT / 2 - 3,
            transformOrigin: "50% 100%",
            transform: "translate(-50%, -100%) rotate(30deg)",
          }}
        >
          {label}
        </span>
      </span>
    </span>
  )
}
