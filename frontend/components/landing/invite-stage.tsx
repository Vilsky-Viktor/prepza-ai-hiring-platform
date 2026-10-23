"use client"

import { cn } from "cn"
import { BellIcon } from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import { ArrivingCandidates } from "@/components/landing/arriving-candidates"
import { InviteCard } from "@/components/landing/invite-card"
import { InterviewHeader } from "@/components/landing/interview-header"
import { Wire } from "@/components/landing/wire"
import { SLACK } from "@/constants/slack"
import {
  DEMO_INVITE_CANDIDATES,
  DEMO_INVITE_INTERVIEW,
  INVITE_NOTIFY_DELAY,
  INVITE_NOTIFY_SPEED,
  INVITE_SOURCES,
  INVITE_WIRE_GAP,
  INVITE_WIRE_INSET,
  type InviteSource,
  INVITE_SPEED,
} from "@/constants/invite-demo"
import { ON_SCREEN, useDemoSteps } from "@/hooks/use-demo-steps"
import { boxOf, sourceWires } from "@/lib/source-wires"

// The cards' places in the stage's list of cards: the sources first, then these two.
const INTERVIEW = INVITE_SOURCES.length
const SLACK_CARD = INTERVIEW + 1
const CARDS = SLACK_CARD + 1

/** The interview in the middle and the ways candidates come into it around it, each a small
 * floating card with a wire to the interview and a candidate running along it to it, counted
 * in as they arrive; under the interview, Slack, with a wire from it and a bell running along it.
 * From laptops up the ways sit on both sides at their own heights; below, half in a row above
 * and half below, with a gap in the middle of the lower row for Slack's wire. Plays while on
 * screen; with reduced motion, the wires alone and nothing floats. */
export function InviteStage({
  labels,
  interview,
  developers,
}: {
  labels: Record<InviteSource["key"], string>
  // The pill on the interview card's top edge.
  interview: string
  // Two lines over the interview: what developers can do, and the link to their docs.
  developers: React.ReactNode
}) {
  const { ref, index } = useDemoSteps<HTMLDivElement>(ON_SCREEN)
  const playing = ON_SCREEN[index].name === "playing"
  // The cards as laid out now, by their place (the sources, then the interview's and Slack's),
  // and the observer that redraws the wires whenever one of them, or the stage, changes size.
  const cards = useRef<(HTMLElement | null)[]>([])
  const observer = useRef<ResizeObserver | null>(null)
  const [wires, setWires] = useState<{ sources: string[]; slack?: string }>({
    sources: [],
  })
  // Candidates arrived since it started playing, back to none after a while.
  const [arrived, setArrived] = useState(0)
  const arrive = useCallback(
    () => setArrived((count) => (count + 1) % DEMO_INVITE_CANDIDATES.arrivals),
    []
  )

  // Back to none whenever it stops (off screen).
  const [wasPlaying, setWasPlaying] = useState(playing)

  if (wasPlaying !== playing) {
    setWasPlaying(playing)
    setArrived(0)
  }

  // The wires, from where the cards are laid out now (their float moves them only a little,
  // over the wires' ends), read afresh on every draw: a card that mounts again (a new key, a
  // hot reload) is a new element, and the old one, detached, measures as nothing.
  const draw = useCallback(() => {
    const stage = ref.current
    const placed = cards.current.filter(
      (element): element is HTMLElement =>
        element !== null && element.offsetParent === stage
    )

    if (!stage || placed.length !== CARDS) {
      return
    }

    const card = boxOf(placed[INTERVIEW])
    const next = {
      sources: sourceWires(
        card,
        placed.slice(0, INTERVIEW).map(boxOf),
        INVITE_WIRE_GAP,
        INVITE_WIRE_INSET
      ),
      // From inside the interview's card out to Slack's.
      slack: sourceWires(
        boxOf(placed[SLACK_CARD]),
        [card],
        0,
        INVITE_WIRE_INSET
      )[0],
    }

    // Unchanged wires keep the picture as it is, so a redraw never starts a render loop.
    setWires((wires) =>
      JSON.stringify(wires) === JSON.stringify(next) ? wires : next
    )
  }, [ref])

  // Draws once the stage is there and the fonts have loaded, then on every change of size.
  useEffect(() => {
    const stage = ref.current

    if (!stage) {
      return
    }

    const watching = new ResizeObserver(draw)
    let live = true

    observer.current = watching

    for (const element of [stage, ...cards.current]) {
      if (element) {
        watching.observe(element)
      }
    }

    void document.fonts.ready.then(() => live && draw())

    return () => {
      live = false
      observer.current = null
      watching.disconnect()
    }
  }, [ref, draw])

  // Each card's ref, the same function on every render: it keeps the card by its place and
  // watches its size from when it mounts until it unmounts.
  const holders = useMemo(
    () =>
      Array.from(
        { length: CARDS },
        (_, at) => (element: HTMLElement | null) => {
          if (!element) {
            return
          }

          cards.current[at] = element
          observer.current?.observe(element)

          return () => {
            observer.current?.unobserve(element)

            if (cards.current[at] === element) {
              cards.current[at] = null
            }
          }
        }
      ),
    []
  )

  const list = (
    sources: readonly InviteSource[],
    offset: number,
    className: string
  ) => (
    <ul aria-hidden className={cn("grid gap-2 lg:contents", className)}>
      {sources.map((source, at) => (
        <InviteCard
          key={source.key}
          ref={holders[offset + at]}
          mark={source.key}
          label={labels[source.key]}
          style={
            {
              "--x": `${source.x}%`,
              "--y": `${source.y}%`,
              "--float": `${source.sway}s`,
              "--phase": `${-source.phase}s`,
            } as React.CSSProperties
          }
          className={cn(
            "lg:absolute lg:top-(--y)",
            source.side === "start" ? "lg:start-(--x)" : "lg:end-(--x)",
            playing &&
              "lg:motion-safe:animate-[source-float_var(--float)_ease-in-out_var(--phase)_infinite]"
          )}
        />
      ))}
    </ul>
  )

  return (
    <div ref={ref} className="relative flex flex-col gap-12 lg:block lg:h-140">
      {/* Drawn anew as it starts playing, so the travellers start then, each after its delay. */}
      <svg
        key={String(playing)}
        aria-hidden
        className="pointer-events-none absolute inset-0 size-full overflow-visible text-ring"
      >
        {wires.sources.map((d, at) => (
          <Wire
            key={INVITE_SOURCES[at].key}
            d={d}
            delay={INVITE_SOURCES[at].delay}
            fired={playing ? undefined : 0}
            traveller="candidate"
            speed={INVITE_SPEED}
            onArrive={arrive}
          />
        ))}
        {wires.slack && (
          <Wire
            d={wires.slack}
            delay={INVITE_NOTIFY_DELAY}
            fired={playing ? undefined : 0}
            traveller={[BellIcon]}
            speed={INVITE_NOTIFY_SPEED}
          />
        )}
      </svg>
      {/* Over the interview from laptops up; above the picture on phones, clear of the wires. */}
      <div className="flex flex-col items-center gap-1.5 lg:absolute lg:inset-x-0 lg:bottom-[calc(100%-9rem)]">
        {developers}
      </div>
      {list(
        INVITE_SOURCES.slice(0, 4),
        0,
        "grid-cols-[repeat(4,minmax(0,1fr))]"
      )}
      <div
        ref={holders[INTERVIEW]}
        data-testid="invite-interview"
        aria-hidden
        className="relative z-10 mx-auto w-full max-w-88 space-y-5 rounded-xl bg-muted p-6 text-start lg:absolute lg:inset-x-0 lg:top-56 lg:mx-auto dark:bg-card"
      >
        {/* What the card is, on its top edge. */}
        <span className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border bg-background px-4 py-1 text-sm text-muted-foreground lowercase">
          {interview}
        </span>
        <InterviewHeader {...DEMO_INVITE_INTERVIEW} large />
        <ArrivingCandidates arrived={arrived} />
      </div>
      {/* The middle column stays empty on phones, for Slack's wire. */}
      {list(
        INVITE_SOURCES.slice(4),
        4,
        "grid-cols-[repeat(2,minmax(0,1fr))_1.5rem_repeat(2,minmax(0,1fr))] [&>li:nth-child(3)]:col-start-4"
      )}
      <ul aria-hidden className="contents">
        <InviteCard
          ref={holders[SLACK_CARD]}
          mark="slack"
          label={SLACK.name}
          className="-mt-6 w-[calc((100%-3rem)/4)] self-center lg:absolute lg:inset-x-0 lg:bottom-0 lg:mx-auto lg:mt-0 lg:w-fit"
        />
      </ul>
    </div>
  )
}
