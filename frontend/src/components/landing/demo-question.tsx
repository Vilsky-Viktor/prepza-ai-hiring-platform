"use client"

import { cn } from "cn"
import { CheckIcon, CornerRightDownIcon, TimerIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { CodeEditor } from "@/components/code-editor"
import { DemoLogo } from "@/components/landing/demo-logo"
import { useStill } from "@/hooks/use-still"
import { MultiChoiceTag } from "@/components/questions/multi-choice-tag"
import { buttonVariants } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  DEMO_QUESTION_SECONDS,
  DEMO_SECTION_QUESTIONS,
  DEMO_SECTIONS,
  type DemoQuestion as Question,
} from "@/constants/candidates-demo"
import type { CodeToken } from "@/lib/code-tokens"
import { clock } from "@/lib/countdown"
import { Dot } from "@/components/dot"

/** A question as a candidate plays it, small, for the landing: the company's logo, the topic,
 * the clock and the progress; the multi-choice tag and hint on a multi-answer question; its text and example; the
 * options, the `picked` ones marked; and Next, once something is picked, at the bottom. The
 * clock runs while `active`. */
export function DemoQuestion({
  question,
  exampleColors,
  picked,
  active,
  optionRefs,
  nextRef,
  pressed,
}: {
  question: Question
  exampleColors: CodeToken[][] | null
  picked: number[]
  active: boolean
  optionRefs: React.RefObject<HTMLLIElement | null>[]
  nextRef: React.Ref<HTMLSpanElement>
  pressed: boolean
}) {
  const t = useTranslations("session")
  const rounds = useTranslations("rounds")

  return (
    <div className="flex flex-1 flex-col gap-5">
      {/* The company's logo on the left of the topic and the progress; above them on phones. */}
      <div className="flex gap-4 max-sm:flex-col sm:items-center">
        <DemoLogo className="size-12" />
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
            <p className="flex min-w-0 items-center">
              <span className="truncate">{question.topic}</span>
              <Dot className="max-sm:hidden" />
              <span className="shrink-0 tabular-nums max-sm:hidden">
                {t("section", {
                  number: question.section,
                  count: DEMO_SECTIONS,
                })}
              </span>
            </p>
            <p className="flex shrink-0 items-center tabular-nums">
              <DemoClock running={active} />
              <Dot />
              {question.answered} / {DEMO_SECTION_QUESTIONS}
            </p>
          </div>
          <Progress
            value={(question.answered / DEMO_SECTION_QUESTIONS) * 100}
          />
        </div>
      </div>
      <div className="space-y-3">
        {question.multi && <MultiChoiceTag />}
        <p className="text-lg leading-snug font-medium sm:text-xl">
          {question.text}
        </p>
        {question.example && (
          <CodeEditor
            code={question.example.code}
            language={question.example.language}
            tokens={[exampleColors]}
            header={false}
            // Compact, so the example doesn't make the picture tall.
            className="[&_pre]:py-2.5 [&_pre]:text-xs [&_pre]:leading-normal"
          />
        )}
      </div>
      {question.multi && (
        <p className="-mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
          {t("selectAll")}
          <CornerRightDownIcon className="size-4 text-primary rtl:-scale-x-100" />
        </p>
      )}
      {/* A practical question's short answers two by two, from tablets up. */}
      <ul className={cn("grid gap-2", question.example && "sm:grid-cols-2")}>
        {question.options.map((option, index) => {
          const chosen = picked.includes(index)

          return (
            <li
              key={option}
              ref={optionRefs[index]}
              className={cn(
                "flex items-center gap-3 rounded-xl border px-4 py-2.5 text-base font-light transition-colors",
                chosen && "border-ring bg-surface"
              )}
            >
              {/* A big check box on a multi-answer question, as when playing it. */}
              {question.multi && (
                <span
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-md border-2 border-input transition-colors",
                    chosen &&
                      "border-primary bg-primary-gradient text-primary-foreground gradient-soft"
                  )}
                >
                  {chosen && <CheckIcon className="size-3.5" strokeWidth={3} />}
                </span>
              )}
              <span className="w-4 shrink-0 text-muted-foreground">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="min-w-0 flex-1">{option}</span>
            </li>
          )
        })}
      </ul>
      {/* Next, at the same place on every question, unseen until something's picked. */}
      <div className="mt-auto flex justify-end">
        <span
          ref={nextRef}
          className={buttonVariants({
            className: cn(
              "h-10 px-5 text-base transition-opacity",
              picked.length === 0 && "opacity-0",
              pressed && "ring-3 ring-ring/50"
            ),
          })}
        >
          {rounds("next")}
        </span>
      </div>
    </div>
  )
}

/** The question's clock, counting down a second at a time while `running`; from the full time
 * again each time it starts. Still with reduced motion or paused. */
function DemoClock({ running }: { running: boolean }) {
  const [left, setLeft] = useState(DEMO_QUESTION_SECONDS)
  const still = useStill()
  const [wasRunning, setWasRunning] = useState(running)

  if (wasRunning !== running) {
    setWasRunning(running)

    if (running) {
      setLeft(DEMO_QUESTION_SECONDS)
    }
  }

  useEffect(() => {
    if (!running || still) {
      return
    }

    const timer = window.setInterval(
      () => setLeft((seconds) => Math.max(0, seconds - 1)),
      1000
    )

    return () => window.clearInterval(timer)
  }, [running, still])

  return (
    <span className="flex items-center gap-1.5 font-medium">
      <TimerIcon className="size-4" />
      {clock(left)}
    </span>
  )
}
