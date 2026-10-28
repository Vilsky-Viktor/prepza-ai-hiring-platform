"use client"

import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"

import { PassStatus } from "@/components/company/pass-status"
import { Dot, Dotted } from "@/components/dot"
import { DemoReportActions } from "@/components/landing/demo-share"
import { AnswerOptions } from "@/components/questions/answer-options"
import { MultiChoiceTag } from "@/components/questions/multi-choice-tag"
import { Badge } from "@/components/ui/badge"
import {
  DEMO_OPENED,
  DEMO_PASS_MARK,
  DEMO_REPORT_CANDIDATES,
  DEMO_REPORT_TOPICS,
  type DemoAnswer,
  type DemoTopic,
} from "@/constants/reports-demo"
import { WARNING_TONE } from "@/constants/tones"
import { useElementSize } from "@/hooks/use-element-size"
import { formatPercent } from "@/lib/format"
import { gradeTone } from "@/lib/grade-tone"

const candidate = DEMO_REPORT_CANDIDATES[DEMO_OPENED]

/** A candidate's report page, small, for the landing: their email, name and status with the
 * report's actions, then, in a window of its own, the grade card, each topic's grade, and the
 * topics with their integrity line and answers. The window scrolls `scrolled` of the way down
 * (0 to 1), smoothly while `gliding`. */
export function DemoReport({
  scrolled,
  gliding,
  shareRef,
  sharePressed,
}: {
  scrolled: number
  gliding: boolean
  shareRef: React.Ref<HTMLSpanElement>
  sharePressed: boolean
}) {
  const t = useTranslations("candidates")
  const statuses = useTranslations("candidateStatus")
  const locale = useLocale()
  const { ref: windowRef, size: windowSize } = useElementSize<HTMLDivElement>()
  const { ref: contentRef, size: contentSize } =
    useElementSize<HTMLDivElement>()
  const room =
    windowSize && contentSize
      ? Math.max(0, contentSize.height - windowSize.height)
      : 0

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex items-start justify-between gap-2 px-1 pt-1">
        <div className="min-w-0 space-y-1">
          <p className="font-heading text-lg font-medium break-all sm:truncate sm:text-xl">
            {candidate.email}
          </p>
          <div className="flex items-center gap-3">
            <span className="truncate text-sm text-muted-foreground">
              {candidate.name}
            </span>
            <Badge variant="outline" className="h-6 px-2.5 text-sm font-light">
              {statuses(candidate.status)}
            </Badge>
          </div>
        </div>
        <DemoReportActions shareRef={shareRef} pressed={sharePressed} />
      </div>
      {/* The page below the header, scrolled inside its own window. */}
      <div
        ref={windowRef}
        className="relative min-h-0 flex-1 overflow-hidden rounded-xl"
      >
        <div
          ref={contentRef}
          style={{ transform: `translateY(${-room * scrolled}px)` }}
          className={cn(
            "absolute inset-x-0 top-0 space-y-6",
            gliding && "transition-transform duration-2000 ease-in-out"
          )}
        >
          <div className="mx-auto flex w-fit items-center divide-x rounded-xl border max-sm:w-full max-sm:flex-col max-sm:divide-x-0 max-sm:py-2">
            <div className="flex items-baseline gap-3 px-6 py-4 max-sm:py-2">
              <p
                className={cn(
                  "text-4xl font-light tabular-nums sm:text-5xl",
                  gradeTone(candidate.passed)
                )}
              >
                {formatPercent(candidate.grade, locale)}
              </p>
              <p className="text-muted-foreground">{t("grade")}</p>
            </div>
            <p className="px-6 py-4 text-base max-sm:py-2">
              <PassStatus passed={candidate.passed} passMark={DEMO_PASS_MARK} />
            </p>
          </div>
          <p className="text-center text-sm text-muted-foreground tabular-nums">
            <Dotted
              items={DEMO_REPORT_TOPICS.map((topic) => (
                <span key={topic.title} className="whitespace-nowrap">
                  {topic.title}{" "}
                  <span className="text-foreground">
                    {formatPercent(topic.grade, locale)}
                  </span>
                </span>
              ))}
            />
          </p>
          {DEMO_REPORT_TOPICS.map((topic) => (
            <DemoTopicAnswers key={topic.title} topic={topic} />
          ))}
        </div>
      </div>
    </div>
  )
}

/** A topic of the report: its title and integrity line, its grade, and its answers. */
function DemoTopicAnswers({ topic }: { topic: DemoTopic }) {
  const t = useTranslations("candidates")
  const locale = useLocale()
  const signals = [
    [t("pageLeaves", { count: topic.tab_leaves }), topic.tab_leaves],
    [t("copies", { count: topic.copies }), topic.copies],
    [t("fastAnswers", { count: topic.fast_answers }), topic.fast_answers],
  ] as const

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className="font-heading text-lg font-medium">{topic.title}</p>
          <p className="flex flex-wrap items-center gap-x-1.5 text-xs text-muted-foreground tabular-nums">
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
            "text-3xl font-light tabular-nums",
            gradeTone(topic.grade >= DEMO_PASS_MARK)
          )}
        >
          {formatPercent(topic.grade, locale)}
        </p>
      </div>
      <ul className="divide-y rounded-xl border">
        {topic.answers.map((answer) => (
          <DemoAnswerItem key={answer.text} answer={answer} />
        ))}
      </ul>
    </section>
  )
}

/** One answer of the report: the question (tagged when it's multi-answer), its verdict in the
 * scorecard's colours (partly correct in the warnings' amber), and what was picked; a
 * multi-answer one's ticks marked right or wrong, with its points. */
function DemoAnswerItem({ answer }: { answer: DemoAnswer }) {
  const rounds = useTranslations("rounds")

  return (
    <li className="space-y-3 p-4">
      {/* On phones the verdict sits above the question, centred, as in the real report. */}
      <div className="flex items-start justify-between gap-3 max-sm:flex-col-reverse max-sm:items-center">
        <div className="min-w-0 space-y-2 max-sm:self-stretch">
          {answer.multi && <MultiChoiceTag />}
          <p className="text-base font-light">{answer.text}</p>
        </div>
        <span
          data-verdict={answer.verdict}
          className={cn(
            "shrink-0 text-base font-light",
            answer.verdict === "partlyCorrect"
              ? WARNING_TONE
              : gradeTone(answer.verdict === "correct")
          )}
        >
          {rounds(answer.verdict)}
        </span>
      </div>
      {answer.multi ? (
        <div className="space-y-2">
          <AnswerOptions
            options={answer.picks}
            className="rounded-xl bg-surface px-4 py-3 text-base font-light"
          />
          <p className="text-sm text-muted-foreground tabular-nums">
            <Dotted
              items={[
                rounds("rightPicks", answer.multi),
                rounds("points", { points: answer.multi.points }),
              ]}
            />
          </p>
        </div>
      ) : (
        <p className="rounded-xl bg-surface px-4 py-3 text-base font-light">
          {answer.picks[0].answer}
        </p>
      )}
    </li>
  )
}
