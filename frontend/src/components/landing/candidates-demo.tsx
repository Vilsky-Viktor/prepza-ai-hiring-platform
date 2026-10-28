"use client"

import { cn } from "cn"
import { createRef, useRef, useState } from "react"

import { DemoInvitation } from "@/components/landing/demo-invitation"
import { DemoPanel } from "@/components/landing/demo-panel"
import { DemoPointer } from "@/components/landing/demo-pointer"
import { DemoQuestion } from "@/components/landing/demo-question"
import {
  DEMO_QUESTIONS,
  type DemoQuestion as Question,
} from "@/config/candidates-demo"
import { type DemoStep, pointedAt, useDemoSteps } from "@/hooks/use-demo-steps"
import type { CodeToken } from "@/lib/code-tokens"

// A step and what it shows: the screen (0 the invitation, then each question) and the options
// picked on it so far.
type Step = DemoStep & { screen: number; picked: number[] }

// A question's steps: read, then each pick aimed at and clicked; then Next, but on the last
// question, whose answer stays a while before it all starts again.
function questionSteps(question: Question, screen: number): Step[] {
  const last = screen === DEMO_QUESTIONS.length
  const steps: Step[] = [
    {
      name: `read${screen}`,
      ms: question.example ? 3200 : 1800,
      screen,
      picked: [],
    },
  ]

  question.picks.forEach((option, index) => {
    const before = question.picks.slice(0, index)
    const after = question.picks.slice(0, index + 1)
    steps.push(
      {
        name: `aim${screen}-${index}`,
        ms: 900,
        point: `option${option}`,
        screen,
        picked: before,
      },
      {
        name: `pick${screen}-${index}`,
        ms: 450,
        click: true,
        screen,
        picked: after,
      }
    )
  })

  const picked = question.picks

  if (last) {
    steps.push({ name: "done", ms: 3000, screen, picked })

    return steps
  }

  steps.push(
    { name: `picked${screen}`, ms: 600, screen, picked },
    { name: `aimNext${screen}`, ms: 800, point: "next", screen, picked },
    { name: `next${screen}`, ms: 450, click: true, screen, picked }
  )

  return steps
}

// The pointer reads the invitation and clicks to start; then answers each question in turn.
const STEPS: Step[] = [
  { name: "invite", ms: 1800, point: "title", screen: 0, picked: [] },
  { name: "aimStart", ms: 900, point: "start", screen: 0, picked: [] },
  { name: "start", ms: 450, click: true, screen: 0, picked: [] },
  ...DEMO_QUESTIONS.flatMap((question, index) =>
    questionSteps(question, index + 1)
  ),
]

/** What a candidate sees, played by a pointer in one panel: the invitation, accepted, then a
 * single-answer question, a multi-answer one and a practical one, each answered. The screens
 * lie on top of each other, so the panel is as tall as the tallest and never changes size; one
 * fades out and the next in. With reduced motion, the last question, answered. */
export function CandidatesDemo({
  exampleColors,
}: {
  // Each question's example in its colors, made on the server.
  exampleColors: (CodeToken[][] | null)[]
}) {
  const { ref, index } = useDemoSteps<HTMLDivElement>(STEPS)
  const step = STEPS[index]
  const titleRef = useRef<HTMLParagraphElement>(null)
  const startRef = useRef<HTMLSpanElement>(null)
  // Each question's options and Next, for the pointer.
  const [questionRefs] = useState(() =>
    DEMO_QUESTIONS.map((question) => ({
      options: question.options.map(() => createRef<HTMLLIElement>()),
      next: createRef<HTMLSpanElement>(),
    }))
  )
  const point = pointedAt(STEPS, index)
  const on = questionRefs[step.screen - 1]
  const target =
    point === "title"
      ? titleRef
      : point === "start"
        ? startRef
        : point === "next"
          ? (on?.next ?? null)
          : point?.startsWith("option")
            ? (on?.options[Number(point.slice("option".length))] ?? null)
            : null

  // A screen, shown while it's the step's, fading in after the one before has faded out.
  function screen(number: number, content: React.ReactNode) {
    const shown = step.screen === number

    return (
      <div
        key={number}
        className={cn(
          "flex flex-col transition-[opacity,translate,visibility]",
          shown
            ? "delay-200 duration-500"
            : "invisible translate-y-2 opacity-0 duration-200"
        )}
      >
        {content}
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-5xl">
      <DemoPanel ref={ref}>
        <DemoPointer
          target={target}
          clicking={step.click === true}
          click={index}
        />
        <div className="grid grid-cols-[minmax(0,1fr)] p-2 *:min-w-0 *:[grid-area:1/1] sm:p-5">
          {screen(
            0,
            <DemoInvitation
              titleRef={titleRef}
              startRef={startRef}
              pressed={step.name === "start"}
            />
          )}
          {DEMO_QUESTIONS.map((question, at) =>
            screen(
              at + 1,
              <DemoQuestion
                question={question}
                exampleColors={exampleColors[at]}
                // Unseen, a question keeps all its picks, so it fades out as it was left.
                picked={step.screen === at + 1 ? step.picked : question.picks}
                active={step.screen === at + 1}
                optionRefs={questionRefs[at].options}
                nextRef={questionRefs[at].next}
                pressed={step.name === `next${at + 1}`}
              />
            )
          )}
        </div>
      </DemoPanel>
    </div>
  )
}
