"use client"

import { cn } from "cn"
import { CheckIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"

import { DemoAnswerPatterns } from "@/features/landing/components/demo-answer-patterns"
import { DemoReportActions } from "@/features/landing/components/demo-share"
import { Dot } from "@/components/common/dot"
import { GradeBlock, GradeCard } from "@/components/common/grade-card"
import { PassStatus } from "@/components/common/pass-status"
import { ScorecardItem } from "@/components/common/scorecard-review"
import { InfoCard } from "@/components/common/warning-card"
import { Badge } from "@/components/ui/badge"
import { LIST_BOX } from "@/config/lists"
import {
  DEMO_PASS_MARK,
  type DemoCandidate,
  type DemoTopic,
} from "@/config/reports-demo"
import { WARNING_TONE } from "@/config/tones"
import { useElementSize } from "@/hooks/use-element-size"
import { formatPercent } from "@/lib/format"
import { gradeTone } from "@/lib/grade-tone"
import type { ReviewItem } from "@/types/round"

// The interview's language, for its questions.
const LANGUAGE = "en"

/** A topic's question as the scorecard gives it (types/round.ts). */
function reviewItem(topic: DemoTopic): ReviewItem | null {
  const question = topic.question

  if (!question) {
    return null
  }

  return {
    question_id: topic.title,
    number: 1,
    text: question.text,
    options: question.options,
    multi: false,
    limit_seconds: 60,
    correct_option_index: question.right,
    answer: {
      answer_id: topic.title,
      option_index: question.pick,
      picks: [question.pick],
      timed_out: false,
      correct: question.pick === question.right,
      seconds: question.seconds,
      fast: question.fast ?? false,
    },
    tab_leaves: question.tab_leaves ?? 0,
    copies: question.copies ?? 0,
  }
}

/** A candidate's page (app/companies/[companyId]/interviews/[id]/candidates/[inviteId]), for
 * the landing, scrolled down `scrolled` pixels (gliding there and back) inside the picture:
 * their email, name and status with the report's actions (the share `pressed` in); the grade
 * card with whether they passed and their pledge; the note that people decide; what their
 * answers show, when anything stood out; then each topic with its signals and grade, and one of
 * its questions as they answered it. */
export function DemoReport({
  candidate,
  scrolled,
  pressed,
}: {
  candidate: DemoCandidate
  scrolled: number
  pressed: boolean
}) {
  const t = useTranslations("candidates")
  const report = useTranslations("report")
  const statuses = useTranslations("candidateStatus")
  const locale = useLocale()
  const { ref: windowRef, size: windowSize } = useElementSize<HTMLDivElement>()
  const { ref: pageRef, size: pageSize } = useElementSize<HTMLDivElement>()
  const room =
    windowSize && pageSize
      ? Math.max(0, pageSize.height - windowSize.height)
      : 0
  const by = Math.min(room, scrolled)
  const signals =
    candidate.tab_leaves + candidate.copies + candidate.fast_answers

  return (
    <div ref={windowRef} className="relative min-h-0 flex-1 overflow-hidden">
      <div
        ref={pageRef}
        style={{ transform: `translateY(${-by}px)` }}
        className="absolute inset-x-0 top-0 space-y-8 transition-transform duration-2000 ease-in-out motion-reduce:transition-none"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0 space-y-1">
            <p className="font-heading text-3xl font-medium tracking-tight break-all">
              {candidate.email}
            </p>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="text-lg">{candidate.name}</span>
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {statuses(candidate.status)}
              </Badge>
            </div>
          </div>
          <DemoReportActions pressed={pressed ? "share" : null} />
        </div>
        <GradeCard>
          <GradeBlock
            value={formatPercent(candidate.grade, locale)}
            label={t("grade")}
            tone={gradeTone(candidate.passed)}
          />
          <div className="flex flex-col justify-center gap-1 px-8 py-6 text-base max-sm:items-center">
            <PassStatus passed={candidate.passed} passMark={DEMO_PASS_MARK} />
            <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <CheckIcon aria-hidden className="size-4 shrink-0" />
              {report("pledged")}
            </p>
          </div>
        </GradeCard>
        <InfoCard className="text-sm">
          {signals ? report("humanReviewSignals") : report("humanReview")}
        </InfoCard>
        {candidate.patterns && (
          <DemoAnswerPatterns patterns={candidate.patterns} />
        )}
        {candidate.topics?.map((topic) => (
          <DemoTopicSection key={topic.title} topic={topic} />
        ))}
      </div>
    </div>
  )
}

/** A topic on the page: its heading, its integrity line (features/company/components/
 * integrity-line.tsx) and grade, then its question as answered, in the real scorecard's row. */
function DemoTopicSection({ topic }: { topic: DemoTopic }) {
  const t = useTranslations("candidates")
  const locale = useLocale()
  const item = reviewItem(topic)
  const signals = [
    [t("pageLeaves", { count: topic.tab_leaves }), topic.tab_leaves],
    [t("copies", { count: topic.copies }), topic.copies],
    [t("fastAnswers", { count: topic.fast_answers }), topic.fast_answers],
  ] as const

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 space-y-1">
          <p className="font-heading text-2xl font-medium">{topic.title}</p>
          <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-muted-foreground tabular-nums">
            {signals.map(([signal, count], index) => (
              <span key={signal} className="flex items-center gap-x-1.5">
                {index > 0 && <Dot className="mx-0" />}
                <span className={cn(count > 0 && WARNING_TONE)}>{signal}</span>
              </span>
            ))}
          </p>
        </div>
        <p
          className={cn(
            "text-5xl font-light tabular-nums",
            gradeTone(topic.grade >= DEMO_PASS_MARK)
          )}
        >
          {formatPercent(topic.grade, locale)}
        </p>
      </div>
      {item && (
        <div className={LIST_BOX}>
          <ScorecardItem item={item} language={LANGUAGE} />
        </div>
      )}
    </section>
  )
}
