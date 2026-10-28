"use client"

import { cn } from "cn"
import {
  CpuAiIcon,
  FlagIcon,
  ListChecksIcon,
  PenLineIcon,
  ScanSearchIcon,
  SparklesIcon,
} from "lucide-react"
import { useEffect, useId, useRef, useState } from "react"

import { useStill } from "@/hooks/use-still"
import { NetOutside } from "@/components/landing/net-outside"
import { NetWave } from "@/components/landing/net-wave"
import { Wire, wireLength } from "@/components/landing/wire"
import { INVITE_SPEED } from "@/constants/invite-demo"
import {
  NET_CELL,
  NET_WAVE_SECONDS,
  NET_WAVES,
  QUALITY_CARD_PADDING,
  QUALITY_ELLIPSE,
  QUALITY_PAUSE_MS,
  QUALITY_STEPS,
  type QualityStep,
} from "@/constants/trust-quality-demo"
import { ON_SCREEN, useDemoSteps } from "@/hooks/use-demo-steps"
import { ellipsePoints, ellipseWires } from "@/lib/ellipse-wires"
import { type Area, sectionArea } from "@/lib/section-area"

const ICONS = {
  generated: SparklesIcon,
  checked: ScanSearchIcon,
  answered: ListChecksIcon,
  flagged: FlagIcon,
  rewritten: PenLineIcon,
}

// Each step's centre on the ellipse, in percent of the stage.
const PLACES = ellipsePoints(
  QUALITY_STEPS.length,
  QUALITY_ELLIPSE.x,
  QUALITY_ELLIPSE.y
)

/** How a question gets better: written, checked, answered, flagged and rewritten, five cards of
 * one size spaced evenly round an ellipse, wired one to the next along it, the last back to the
 * first. While on screen a question runs round it, resting on each step, which lights up; with
 * reduced motion, the ring alone. Right to left, the ring mirrors. */
export function QualityLoop({
  labels,
  lines,
}: {
  labels: Record<QualityStep, string>
  lines: Record<QualityStep, string>
}) {
  const { ref, index } = useDemoSteps<HTMLDivElement>(ON_SCREEN)
  const playing = ON_SCREEN[index].name === "playing"
  const contents = useRef<HTMLElement[]>([])
  // The net pattern's id, letters and digits only, for an SVG url().
  const net = `net-${useId().replace(/[^a-zA-Z0-9]/g, "")}`
  const [wires, setWires] = useState<string[]>([])
  // The stage's size, in pixels, for the net inside the ellipse.
  // The stage's size, in pixels, for the net inside the ellipse, and the section's box across the
  // page in the stage's frame, for the net outside it.
  const [size, setSize] = useState<{
    width: number
    height: number
    area: Area
  } | null>(null)
  // The step the question is on, and how many times each wire has sent it on.
  const [lit, setLit] = useState<number | null>(null)
  const still = useStill()
  const [fired, setFired] = useState<number[]>(QUALITY_STEPS.map(() => 0))

  // The ellipse's arcs through the cards' centres and the cards' one height, the tallest card's
  // content and its padding, again whenever the stage or a card's content changes size.
  useEffect(() => {
    const stage = ref.current

    if (!stage) {
      return
    }

    function draw() {
      const { offsetWidth: width, offsetHeight: height } = stage!
      const tallest = Math.max(
        ...contents.current.map((content) => content.offsetHeight)
      )
      stage!.style.setProperty(
        "--card-h",
        `${tallest + QUALITY_CARD_PADDING}px`
      )
      setSize({ width, height, area: sectionArea(stage!) })
      const mirrored = getComputedStyle(stage!).direction === "rtl"
      // From the stage's centre, the drawing's origin: a traveller waiting between runs sits
      // there, behind the chip, rather than on the stage's corner, past the window's edge.
      const points = PLACES.map(({ x, y }) => ({
        x: ((mirrored ? 50 - x : x - 50) * width) / 100,
        y: ((y - 50) * height) / 100,
      }))
      setWires(
        ellipseWires(
          points,
          { x: 0, y: 0 },
          (QUALITY_ELLIPSE.x * width) / 100,
          (QUALITY_ELLIPSE.y * height) / 100
        )
      )
    }

    const observer = new ResizeObserver(draw)

    // The page's body too: on a wide window the stage keeps its size while the page grows.
    for (const element of [stage, document.body, ...contents.current]) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [ref])

  // Round the ring: a rest on a step, then the wire to the next, which takes as long as it's long.
  useEffect(() => {
    if (!playing || wires.length === 0 || still) {
      return
    }

    let timer: number | undefined

    function rest(step: number) {
      setLit(step)
      timer = window.setTimeout(() => {
        setFired((counts) =>
          counts.map((count, at) => (at === step ? count + 1 : count))
        )
        timer = window.setTimeout(
          () => rest((step + 1) % wires.length),
          (wireLength(wires[step]) / INVITE_SPEED) * 1000
        )
      }, QUALITY_PAUSE_MS)
    }

    rest(0)

    // Off screen, no step is lit.
    return () => {
      window.clearTimeout(timer)
      setLit(null)
    }
  }, [playing, wires, still])

  return (
    <div
      ref={ref}
      aria-hidden
      className="relative mx-auto h-[26rem] w-full max-w-md lg:h-[37rem] lg:max-w-6xl"
    >
      {/* Drawn anew as the light starts, so the waves' clock starts with the chip's charging. */}
      <svg
        key={String(playing && !still)}
        className="pointer-events-none absolute inset-0 size-full overflow-visible text-ring"
      >
        {/* The net: a fine diamond mesh in the primary colour, inside the ellipse. */}
        <defs>
          <pattern
            id={net}
            width={NET_CELL}
            height={NET_CELL}
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <path
              d={`M 0 0 H ${NET_CELL} M 0 0 V ${NET_CELL}`}
              fill="none"
              strokeWidth={1}
              className="stroke-primary/15 dark:stroke-primary/25"
            />
          </pattern>
        </defs>
        {size && (
          <NetOutside
            cx={size.width / 2}
            cy={size.height / 2}
            rx={(QUALITY_ELLIPSE.x * size.width) / 100}
            ry={(QUALITY_ELLIPSE.y * size.height) / 100}
            width={size.width}
            area={size.area}
            cell={NET_CELL}
          />
        )}
        {size && (
          <ellipse
            cx={size.width / 2}
            cy={size.height / 2}
            rx={(QUALITY_ELLIPSE.x * size.width) / 100}
            ry={(QUALITY_ELLIPSE.y * size.height) / 100}
            fill={`url(#${net})`}
          />
        )}
        {size && playing && !still && (
          <NetWave
            cx={size.width / 2}
            cy={size.height / 2}
            rx={(QUALITY_ELLIPSE.x * size.width) / 100}
            ry={(QUALITY_ELLIPSE.y * size.height) / 100}
            from={40}
            cell={NET_CELL}
          />
        )}
        {/* The wires, drawn from the stage's centre, where a traveller waits between runs. Only
            they move the origin: the net's mask and blur keep their regions on the stage. */}
        <g
          transform={
            size ? `translate(${size.width / 2} ${size.height / 2})` : undefined
          }
        >
          {wires.map((d, at) => (
            <Wire
              key={at}
              d={d}
              fired={fired[at]}
              traveller="comet"
              thickness={1.5}
              speed={INVITE_SPEED}
            />
          ))}
        </g>
      </svg>
      {/* The AI chip at the ellipse's centre, half lit; while the light runs, it charges to full
          just as each wave leaves it through the net, then dims again (one charge a wave, on the
          waves' clock). */}
      <span
        data-testid="ai-chip"
        className="absolute top-1/2 left-1/2 flex size-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center text-primary lg:size-36"
      >
        <CpuAiIcon
          className={cn(
            "relative size-16 lg:size-24",
            size && playing && !still
              ? "animate-[chip-charge_ease-in-out_infinite]"
              : "opacity-50"
          )}
          style={{
            animationDuration: `${NET_WAVE_SECONDS / NET_WAVES}s`,
          }}
          strokeWidth={1.5}
        />
      </span>
      {QUALITY_STEPS.map((key, at) => {
        const Icon = ICONS[key]

        return (
          <div
            key={key}
            data-testid="quality-step"
            data-lit={lit === at || undefined}
            style={
              {
                "--x": `${PLACES[at].x}%`,
                "--y": `${PLACES[at].y}%`,
              } as React.CSSProperties
            }
            className={cn(
              "absolute start-(--x) top-(--y) z-10 flex size-24 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center gap-2 rounded-xl border p-1.5 pt-6 text-center lowercase transition-shadow duration-300 lg:h-(--card-h) lg:w-60 lg:justify-start lg:p-5 lg:pt-9 rtl:translate-x-1/2",
              // The page's colour, see-through as much as the interview card among the ways in.
              "bg-background/75",
              lit === at && "border-primary-gradient"
            )}
          >
            {/* The step's icon, sitting on the card's top edge. */}
            <span className="absolute top-0 left-1/2 flex size-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-xl border bg-background text-foreground lg:size-12 [&_svg]:size-5 lg:[&_svg]:size-6">
              <Icon />
            </span>
            <span
              ref={(element) => {
                if (element) {
                  contents.current[at] = element
                }
              }}
              className="flex min-w-0 shrink-0 flex-col items-center"
            >
              <span className="flex min-w-0 flex-col gap-1">
                <span className="font-heading text-sm font-medium break-words lg:text-lg">
                  {labels[key]}
                </span>
                <span className="hidden text-sm leading-snug text-muted-foreground normal-case lg:block">
                  {lines[key]}
                </span>
              </span>
            </span>
          </div>
        )
      })}
    </div>
  )
}
