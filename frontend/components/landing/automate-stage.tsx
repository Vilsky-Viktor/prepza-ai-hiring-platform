"use client"

import { cn } from "cn"
import {
  AppWindowIcon,
  BellIcon,
  BrainIcon,
  BracesIcon,
  BriefcaseBusinessIcon,
  CheckIcon,
  LinkIcon,
  PanelsTopLeftIcon,
  WebhookIcon,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { KeepAcronyms } from "@/components/keep-acronyms"
import { SOURCE_CARD } from "@/components/landing/demo-panel"
import { Wire } from "@/components/landing/wire"
import { Wordmark } from "@/components/wordmark"
import { MCP_MARK } from "@/constants/ai-apps"
import {
  AUTOMATE_CARDS,
  AUTOMATE_DELAYS,
  AUTOMATE_NOTIFY_SPEED,
  AUTOMATE_WIRE_GAP,
  AUTOMATE_WIRE_INSET,
  type AutomateCard,
} from "@/constants/automate-demo"
import { INVITE_SPEED } from "@/constants/invite-demo"
import { SLACK } from "@/constants/slack"
import { ON_SCREEN, useDemoSteps } from "@/hooks/use-demo-steps"
import { type Box, boxOf, reversed, sourceWires } from "@/lib/source-wires"

const ICONS = {
  platform: AppWindowIcon,
  aiApp: BrainIcon,
  api: BracesIcon,
  sdk: PanelsTopLeftIcon,
  webhook: WebhookIcon,
  jobBoard: BriefcaseBusinessIcon,
  link: LinkIcon,
}

// Where each card sits: on phones and tablets the ways in are two rows of a five-column grid
// above prepza and Slack; from laptops up they are two columns on the left, then prepza, then
// Slack, in five rows: the two left columns wide enough for their labels, with flexible gaps
// around them for the wires, and prepza close to Slack.
const PLACES: Record<AutomateCard | "prepza", string> = {
  platform: "col-span-3 col-start-1 row-start-1 lg:col-span-1 lg:row-span-3",
  aiApp: "col-start-4 row-start-1 lg:col-start-1 lg:row-start-4",
  jobBoard: "col-start-5 row-start-1 lg:col-start-1 lg:row-start-5",
  api: "col-start-1 row-start-2 lg:col-start-3 lg:row-start-1",
  sdk: "col-start-2 row-start-2 lg:col-start-3 lg:row-start-2",
  webhook: "col-start-3 row-start-2 lg:col-start-3 lg:row-start-3",
  mcp: "col-start-4 row-start-2 lg:col-start-3 lg:row-start-4",
  link: "col-start-5 row-start-2 lg:col-start-3 lg:row-start-5",
  prepza:
    "col-span-5 row-start-3 lg:col-span-1 lg:col-start-5 lg:row-span-5 lg:row-start-1",
  slack:
    "col-span-5 row-start-4 lg:col-span-1 lg:col-start-6 lg:row-span-5 lg:row-start-1 lg:ms-12",
}

type Traveller = React.ComponentProps<typeof Wire>["traveller"]

/** How other tools work with prepza, wired to it: your platform sends candidates in through the
 * API and the embedded SDK and hears the web hooks' events, an AI app asks the MCP server and gets its answers, candidates come from a job
 * board through the shared ad link, and prepza tells Slack. Plays while on screen; with reduced
 * motion, the wires alone. */
export function AutomateStage({
  labels,
}: {
  labels: Record<AutomateCard, string>
}) {
  const { ref, index } = useDemoSteps<HTMLDivElement>(ON_SCREEN)
  const playing = ON_SCREEN[index].name === "playing"
  const cards = useRef<Partial<Record<AutomateCard | "prepza", HTMLElement>>>(
    {}
  )
  const [wires, setWires] = useState<
    { key: string; d: string; traveller: Traveller; speed?: number }[]
  >([])

  // The wires, from where the cards are laid out, again whenever one of them changes size.
  useEffect(() => {
    const stage = ref.current
    const elements = cards.current

    if (!stage) {
      return
    }

    function draw() {
      const box = (key: AutomateCard | "prepza") => boxOf(elements[key]!)
      const wire = (from: Box, to: Box) =>
        sourceWires(to, [from], 0, AUTOMATE_WIRE_INSET)[0]
      // A card as two boxes a wire's gap apart, for a pair of wires side by side.
      const half = AUTOMATE_WIRE_GAP / 2
      const pair = (key: AutomateCard) =>
        [-half, half].map((by) => {
          const card = box(key)

          return { ...card, left: card.left + by, top: card.top + by }
        })
      const [apiIn, sdkIn, webhookIn, mcpAsk, mcpAnswer, linkIn] = sourceWires(
        box("prepza"),
        [box("api"), box("sdk"), box("webhook"), ...pair("mcp"), box("link")],
        AUTOMATE_WIRE_GAP,
        AUTOMATE_WIRE_INSET
      )
      const [ask, answer] = sourceWires(
        box("mcp"),
        pair("aiApp"),
        AUTOMATE_WIRE_GAP,
        AUTOMATE_WIRE_INSET
      )

      setWires([
        {
          key: "request",
          d: wire(box("platform"), box("api")),
          traveller: "candidate",
        },
        { key: "apiIn", d: apiIn, traveller: "candidate" },
        {
          key: "embed",
          d: wire(box("platform"), box("sdk")),
          traveller: "candidate",
        },
        { key: "sdkIn", d: sdkIn, traveller: "candidate" },
        { key: "webhookOut", d: reversed(webhookIn), traveller: [CheckIcon] },
        {
          key: "event",
          d: wire(box("webhook"), box("platform")),
          traveller: [CheckIcon],
        },
        { key: "ask", d: ask, traveller: "candidate" },
        { key: "answer", d: reversed(answer), traveller: [CheckIcon] },
        { key: "mcpAsk", d: mcpAsk, traveller: "candidate" },
        { key: "mcpAnswer", d: reversed(mcpAnswer), traveller: [CheckIcon] },
        {
          key: "apply",
          d: wire(box("jobBoard"), box("link")),
          traveller: "candidate",
        },
        { key: "linkIn", d: linkIn, traveller: "candidate" },
        {
          key: "notify",
          d: wire(box("prepza"), box("slack")),
          traveller: [BellIcon],
          speed: AUTOMATE_NOTIFY_SPEED,
        },
      ])
    }

    const observer = new ResizeObserver(draw)

    for (const element of [stage, ...Object.values(elements)]) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [ref])

  return (
    <div
      ref={ref}
      aria-hidden
      className="relative grid grid-cols-[repeat(5,minmax(0,1fr))] gap-x-1.5 gap-y-12 lg:grid-cols-[13rem_minmax(0,1fr)_13rem_minmax(0,1fr)_12rem_auto] lg:gap-x-0 lg:gap-y-5"
    >
      {/* Drawn anew as it starts playing, so the travellers start then, each after its delay. */}
      <svg
        key={String(playing)}
        className="pointer-events-none absolute inset-0 size-full overflow-visible text-ring"
      >
        {wires.map((wire) => (
          <Wire
            key={wire.key}
            d={wire.d}
            delay={AUTOMATE_DELAYS[wire.key as keyof typeof AUTOMATE_DELAYS]}
            fired={playing ? undefined : 0}
            traveller={wire.traveller}
            speed={wire.speed ?? INVITE_SPEED}
          />
        ))}
      </svg>
      {AUTOMATE_CARDS.map((key) => (
        <div
          key={key}
          ref={(element) => {
            cards.current[key] = element ?? undefined
          }}
          className={cn(
            SOURCE_CARD,
            PLACES[key],
            "lg:self-center",
            key === "slack" && "w-40 justify-self-center lg:w-auto"
          )}
        >
          <CardMark card={key} />
          <span>
            <KeepAcronyms text={labels[key]} />
          </span>
        </div>
      ))}
      <div
        ref={(element) => {
          cards.current.prepza = element ?? undefined
        }}
        className={cn(
          PLACES.prepza,
          "relative z-10 flex w-full max-w-60 items-center justify-center justify-self-center rounded-3xl bg-muted py-6 lg:self-center lg:py-9 dark:bg-card"
        )}
      >
        <Wordmark className="text-4xl leading-none" />
      </div>
    </div>
  )
}

/** A card's icon, or its logo: Slack's in its colours; the MCP mark, one colour, in the
 * icons' blue like the other cards. */
function CardMark({ card }: { card: AutomateCard }) {
  if (card === "mcp") {
    return (
      <span
        aria-hidden
        className="size-6 shrink-0 bg-primary"
        style={{
          mask: `url(${MCP_MARK}) center / contain no-repeat`,
          WebkitMask: `url(${MCP_MARK}) center / contain no-repeat`,
        }}
      />
    )
  }

  if (card === "slack") {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={SLACK.logo} alt="" className="size-6 shrink-0 object-contain" />
    )
  }

  const Icon = ICONS[card]

  return <Icon className="size-6 shrink-0 text-primary" />
}
