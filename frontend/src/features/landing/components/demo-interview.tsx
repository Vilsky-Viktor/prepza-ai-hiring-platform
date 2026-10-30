"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { DemoInterviewTabs } from "@/features/landing/components/demo-interview-tabs"
import { DemoInterviewTopics } from "@/features/landing/components/demo-interview-topics"
import { InterviewEstimate } from "@/components/common/interview-estimate"
import { InterviewStatus } from "@/components/common/interview-status"
import { buttonVariants } from "@/components/ui/button"
import { DEMO_INTERVIEW } from "@/config/create-demo"

/** A new interview's page (app/companies/[companyId]/interviews/[id]), small: its title with
 * "new candidate" beside it (`invite`, pressed in while `pressed`) and its `status` under it,
 * its tabs as on narrow screens with topics open, what it adds up to for each candidate, and its
 * topics with how many questions each candidate gets of each (`limits`, one `focused`). */
export function DemoInterview({
  topics,
  status,
  limits,
  changed,
  focused,
  pressed,
}: {
  topics: { name: string; subtopics: string[] }[]
  status: string
  limits: Record<string, number>
  changed: string[]
  focused: string | null
  pressed: boolean
}) {
  const t = useTranslations("interviews")
  const { title, topicQuestions, questionSeconds } = DEMO_INTERVIEW
  const questions = Object.values(limits).reduce((sum, n) => sum + n, 0)

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-4">
      <div className="flex items-start justify-between gap-3 px-1">
        <div className="min-w-0 space-y-1.5">
          <p className="font-heading text-xl leading-tight font-medium">
            {title}
          </p>
          <InterviewStatus status="new" label={status} />
        </div>
        <span
          data-demo-target="invite"
          className={buttonVariants({
            className: cn("h-9 shrink-0 px-4", pressed && DEMO_PRESSED),
          })}
        >
          {t("newCandidate")}
        </span>
      </div>
      <DemoInterviewTabs current="topics" counts={{ topics: topics.length }} />
      <InterviewEstimate
        questions={questions}
        questionSeconds={questionSeconds}
        minutes={(questions * questionSeconds) / 60}
        small
      />
      <DemoInterviewTopics
        topics={topics}
        count={topicQuestions}
        limits={limits}
        changed={changed}
        focused={focused}
      />
    </div>
  )
}
