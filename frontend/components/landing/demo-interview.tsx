"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { InterviewEstimate } from "@/components/company/interview-estimate"
import { InterviewHeader } from "@/components/landing/interview-header"
import { buttonVariants } from "@/components/ui/button"
import { DEMO_INTERVIEW } from "@/constants/create-demo"

/** A new interview's page (app/companies/[companyId]/interviews/[id]), small: its title, its
 * `status` and size, what it adds up to for each candidate, its topics with how many questions
 * each candidate gets of each, and right under them the button to invite candidates
 * (`inviteRef`), ringed while `pressed`. */
export function DemoInterview({
  topics,
  status,
  invite,
  inviteRef,
  pressed,
}: {
  topics: string[]
  status: string
  invite: string
  inviteRef?: React.Ref<HTMLSpanElement>
  pressed: boolean
}) {
  const t = useTranslations("questions")
  const { title, topicQuestions, perCandidate, questionSeconds } =
    DEMO_INTERVIEW
  const questions = topics.length * perCandidate

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-3">
      <InterviewHeader
        title={title}
        statusLabel={status}
        topics={topics.length}
        questions={topics.length * topicQuestions}
      />
      <InterviewEstimate
        questions={questions}
        questionSeconds={questionSeconds}
        minutes={(questions * questionSeconds) / 60}
        small
      />
      <ul className="divide-y rounded-2xl border">
        {topics.map((topic) => (
          <li
            key={topic}
            className="flex items-center justify-between gap-3 px-3 py-2"
          >
            <span className="min-w-0 truncate font-medium">{topic}</span>
            <span className="shrink-0 text-xs whitespace-nowrap text-muted-foreground tabular-nums">
              {perCandidate} {t("count", { count: perCandidate })}
            </span>
          </li>
        ))}
      </ul>
      <span
        ref={inviteRef}
        className={buttonVariants({
          className: cn("w-full lowercase", pressed && "ring-3 ring-ring/50"),
        })}
      >
        {invite}
      </span>
    </div>
  )
}
