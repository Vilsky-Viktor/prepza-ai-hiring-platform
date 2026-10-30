"use client"

import { useTranslations } from "next-intl"

import { DemoQuestionCard } from "@/features/landing/components/demo-question"
import { DemoSessionFooter } from "@/features/landing/components/demo-session-footer"
import { DemoSessionHeader } from "@/features/landing/components/demo-session-header"
import type { DemoQuestion } from "@/config/candidates-demo"
import type { CodeToken } from "@/lib/code-tokens"

/** A click-mode question as a candidate plays it (features/company/components/session-play.tsx),
 * for the landing: the header, the question beside its options (stacked on phones), and the
 * footer with Next once an option is `picked`. The clock runs while `active`. */
export function DemoClickSession({
  question,
  exampleColors,
  active,
  picked,
  pressed,
}: {
  question: DemoQuestion
  exampleColors: CodeToken[][] | null
  active: boolean
  picked: number[]
  pressed: boolean
}) {
  const t = useTranslations("session")
  const rounds = useTranslations("rounds")

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6">
      <DemoSessionHeader question={question} active={active} />
      <DemoQuestionCard
        question={question}
        picked={picked}
        exampleColors={exampleColors}
        className="min-h-0 flex-1 content-start overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-start lg:gap-8"
      />
      <DemoSessionFooter
        finish={t("finish")}
        next={rounds("next")}
        picked={picked.length > 0}
        pressed={pressed}
      />
    </div>
  )
}
