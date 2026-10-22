"use client"

import { cn } from "cn"
import {
  ShieldQuestionMarkIcon,
  FlagIcon,
  ListChecksIcon,
  PenLineIcon,
  ScanSearchIcon,
  SparklesIcon,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { SOURCE_CARD } from "@/components/landing/demo-panel"
import { useStill } from "@/hooks/use-still"
import { Wire, wireLength } from "@/components/landing/wire"
import { INVITE_SPEED } from "@/constants/invite-demo"
import {
  QUALITY_PAUSE_MS,
  QUALITY_PLACES,
  QUALITY_STEPS,
  type QualityStep,
  QUESTION_SIZE,
} from "@/constants/trust-quality-demo"
import { ON_SCREEN, useDemoSteps } from "@/hooks/use-demo-steps"
import { loopWires } from "@/lib/loop-wires"

const ICONS = {
  generated: SparklesIcon,
  checked: ScanSearchIcon,
  answered: ListChecksIcon,
  flagged: FlagIcon,
  rewritten: PenLineIcon,
}

/** How a question gets better: written, checked, answered, flagged and rewritten, on a ring of
 * steps wired one to the next, the last back to the first. While on screen a question runs
 * round it, resting on each step, which lights up; with reduced motion, the ring alone. */
export function QualityLoop({
  labels,
  lines,
}: {
  labels: Record<QualityStep, string>
  lines: Record<QualityStep, string>
}) {
  const { ref, index } = useDemoSteps<HTMLDivElement>(ON_SCREEN)
  const playing = ON_SCREEN[index].name === "playing"
  const cards = useRef<Partial<Record<QualityStep, HTMLElement>>>({})
  const [wires, setWires] = useState<string[]>([])
  // The step the question is on, and how many times each wire has sent it on.
  const [lit, setLit] = useState<number | null>(null)
  const still = useStill()
  const [fired, setFired] = useState<number[]>(QUALITY_STEPS.map(() => 0))

  // The wires through the cards' middles, again whenever one of them changes size.
  useEffect(() => {
    const stage = ref.current
    const elements = cards.current

    if (!stage) {
      return
    }

    function draw() {
      setWires(
        loopWires(
          QUALITY_STEPS.map((key) => {
            const card = elements[key]!

            return {
              x: card.offsetLeft + card.offsetWidth / 2,
              y: card.offsetTop + card.offsetHeight / 2,
            }
          })
        )
      )
    }

    const observer = new ResizeObserver(draw)

    for (const element of [stage, ...Object.values(elements)]) {
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
      className="relative mx-auto grid w-full max-w-md grid-cols-3 gap-x-3 gap-y-12 lg:max-w-4xl lg:grid-cols-5 lg:gap-x-4 lg:gap-y-6"
    >
      <svg className="pointer-events-none absolute inset-0 size-full overflow-visible text-ring">
        {wires.map((d, at) => (
          <Wire
            key={at}
            d={d}
            fired={fired[at]}
            traveller={[ShieldQuestionMarkIcon]}
            size={QUESTION_SIZE}
            speed={INVITE_SPEED}
          />
        ))}
      </svg>
      {QUALITY_STEPS.map((key, at) => {
        const Icon = ICONS[key]

        return (
          <div
            key={key}
            ref={(element) => {
              cards.current[key] = element ?? undefined
            }}
            data-lit={lit === at || undefined}
            className={cn(
              SOURCE_CARD,
              QUALITY_PLACES[key],
              "transition-shadow duration-300 lg:flex-col lg:gap-1 lg:py-4 lg:whitespace-normal",
              lit === at && "ring-2 ring-primary"
            )}
          >
            <Icon className="size-6 shrink-0 text-primary" />
            <span>{labels[key]}</span>
            <span className="hidden text-xs leading-snug font-normal text-muted-foreground normal-case lg:block">
              {lines[key]}
            </span>
          </div>
        )
      })}
    </div>
  )
}
