"use client"

import { TimerIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { DemoLogo } from "@/features/landing/components/demo-logo"
import { Count } from "@/components/common/count"
import { Dot } from "@/components/common/dot"
import { Progress } from "@/components/ui/progress"
import {
  DEMO_QUESTION_SECONDS,
  DEMO_SECTION_QUESTIONS,
  DEMO_SECTIONS,
  type DemoQuestion,
} from "@/config/candidates-demo"
import { useStill } from "@/hooks/use-still"
import { clock } from "@/lib/countdown"

/** The interview's header (features/company/components/session-header.tsx), for the landing: the
 * company's logo, the question's topic and section, its clock (running while `active`), the
 * count answered and the progress. */
export function DemoSessionHeader({
  question,
  active,
}: {
  question: DemoQuestion
  active: boolean
}) {
  const t = useTranslations("session")

  return (
    <div className="flex items-center gap-4">
      <DemoLogo className="size-12 max-sm:hidden" />
      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
          <p className="flex min-w-0 items-center">
            <span className="truncate">{question.topic}</span>
            <Dot className="max-sm:hidden" />
            <span className="shrink-0 tabular-nums max-sm:hidden">
              {t("section", { number: question.section, count: DEMO_SECTIONS })}
            </span>
          </p>
          <p className="flex shrink-0 items-center tabular-nums">
            <DemoClock running={active} />
            <Dot />
            <Count done={question.answered} total={DEMO_SECTION_QUESTIONS} />
          </p>
        </div>
        <Progress value={(question.answered / DEMO_SECTION_QUESTIONS) * 100} />
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
