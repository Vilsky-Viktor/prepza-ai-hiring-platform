"use client"

import { cn } from "cn"
import { useState } from "react"

import { CreateDescribe } from "@/features/landing/components/create-describe"
import { CreateReady } from "@/features/landing/components/create-ready"
import { CreateTopics } from "@/features/landing/components/create-topics"
import { DemoPanel } from "@/features/landing/components/demo-panel"
import { DemoPointer } from "@/features/landing/components/demo-pointer"
import { STEPS, TARGETS, TOPICS, WRITING } from "@/config/create-demo-steps"
import { pointedAt, useDemoSteps } from "@/hooks/use-demo-steps"

/** How an interview is created, played in one frame, each screen taking the last one's place: a
 * job description pasted into the home page's box and sent, and a first company named; the
 * topics it gives, adjusted by hand and by asking the AI, then approved; their questions written,
 * then the interview ready, its questions per candidate changed and a candidate invited. A
 * numbered pill on the frame's top edge names the stage. The frame keeps one size as it plays. */
export function CreateFlow({
  labels,
}: {
  labels: {
    // Each stage's title, its number first.
    steps: React.ReactNode[]
    status: string
  }
}) {
  const { ref, ...at } = useDemoSteps<HTMLDivElement>(STEPS)
  const stage = at.index < TOPICS ? 0 : at.index < WRITING ? 1 : 2
  // What the pointer moves to: the element named so in the screen shown, found as the pointer
  // looks for it. Made once, so the pointer only moves when its target does.
  const [targets] = useState(() =>
    Object.fromEntries(
      TARGETS.map((name) => [
        name,
        {
          get current() {
            return (
              ref.current?.querySelector<HTMLElement>(
                `[data-shown=true] [data-demo-target="${name}"]`
              ) ?? null
            )
          },
        },
      ])
    )
  )
  const point = pointedAt(STEPS, at.index)

  // A screen, shown while it's the stage's, fading in after the one before has faded out.
  function screen(number: number, content: React.ReactNode) {
    return (
      <div
        data-shown={stage === number}
        className={cn(
          "relative flex min-h-0 flex-col overflow-hidden transition-[opacity,translate,visibility]",
          stage === number
            ? "delay-200 duration-500"
            : "invisible translate-y-2 opacity-0 duration-200"
        )}
      >
        {content}
      </div>
    )
  }

  return (
    // The stage's title sits on the frame's top edge, a third of it over it, so it never moves
    // the frame; the titles lie on top of each other, crossfading, as wide as the widest.
    <div className="relative">
      <div className="absolute start-1/2 top-0 z-20 grid -translate-x-1/2 -translate-y-2/3 *:[grid-area:1/1] rtl:translate-x-1/2">
        {labels.steps.map((title, index) => (
          <p
            key={index}
            data-testid="create-step"
            data-current={index === stage}
            className={cn(
              "rounded-full border bg-background px-6 py-3 text-center font-heading text-lg font-medium whitespace-nowrap transition-opacity duration-300 sm:text-xl",
              index !== stage && "opacity-0"
            )}
          >
            {title}
          </p>
        ))}
      </div>
      <DemoPanel ref={ref}>
        <DemoPointer
          target={targets[point ?? ""] ?? null}
          clicking={STEPS[at.index].click === true}
          click={at.index}
        />
        {/* One size for every screen, so nothing moves as they change. */}
        <div className="grid h-[44rem] grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] p-2 *:min-w-0 *:[grid-area:1/1] max-sm:h-[40rem] sm:p-5 lg:h-[38rem]">
          {screen(0, <CreateDescribe at={at} />)}
          {screen(
            1,
            <div className="mx-auto flex w-full max-w-3xl min-w-0 flex-1">
              <CreateTopics at={at} />
            </div>
          )}
          {screen(
            2,
            <CreateReady at={at} labels={{ status: labels.status }} />
          )}
        </div>
      </DemoPanel>
    </div>
  )
}
