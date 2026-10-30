import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { Count } from "@/components/common/count"
import { Countdown } from "@/features/company/components/countdown"
import { Progress } from "@/components/ui/progress"
import type { InterviewSession } from "@/types/company"
import type { NextQuestion } from "@/types/round"
import { Dot } from "@/components/common/dot"

type HeaderProps = {
  brand?: ReactNode
  session: InterviewSession
  progress: { answered: number; total: number }
  section: { number: number; count: number }
  // The question waiting for an answer, with its clock.
  question: NextQuestion | null
  // The pick is being sent: the clock runs on, but moves on only once that's done.
  sending: boolean
  // Called when the question's clock reaches zero: the server counts it as wrong, and the
  // next one opens.
  onTimeUp: () => void
}

/** The interview's top, on its click and voice screens alike: the way back (a member's preview)
 * and the header, and the polite line announcing a question whose time ran out. */
export function SessionTop({
  back,
  timedOut,
  ...header
}: HeaderProps & {
  back?: ReactNode
  // The question whose clock ran out, announced to screen readers.
  timedOut: string | null
}) {
  const t = useTranslations("session")

  return (
    <>
      {/* On phones the way back and the logo share a line, the progress under them. */}
      <div className="relative max-sm:flex max-sm:flex-wrap max-sm:items-center max-sm:gap-x-2 max-sm:gap-y-4">
        {back}
        <SessionHeader {...header} />
      </div>
      <p aria-live="polite" className="sr-only">
        {timedOut && <span key={timedOut}>{t("timeUp")}</span>}
      </p>
    </>
  )
}

/** The interview's header: the company's logo, the section's title and place, the question's
 * clock and the progress. */
export function SessionHeader({
  brand,
  session,
  progress,
  section,
  question,
  sending,
  onTimeUp,
}: HeaderProps) {
  const t = useTranslations("session")
  const candidates = useTranslations("candidates")

  // The company's logo on the left of the section's title and the progress bar (above them, on
  // phones, beside the way back).
  return (
    <div className="flex items-center gap-4 max-sm:contents">
      {brand}
      <div className="min-w-0 flex-1 space-y-3 max-sm:basis-full">
        <div className="flex min-w-0 items-center justify-between gap-4">
          <p className="flex min-w-0 items-center text-sm text-muted-foreground">
            <span className="truncate">{session.topic_title}</span>
            {section.count > 1 && (
              <>
                <Dot />
                <span className="shrink-0 tabular-nums">
                  {t("section", {
                    number: section.number,
                    count: section.count,
                  })}
                </span>
              </>
            )}
          </p>
          <p className="flex shrink-0 items-center text-sm text-muted-foreground tabular-nums">
            {question?.seconds_left != null && (
              <>
                <Countdown
                  key={question.question_id}
                  seconds={question.seconds_left}
                  questionSeconds={question.seconds ?? question.seconds_left}
                  paused={sending}
                  onExpire={onTimeUp}
                />
                <Dot />
              </>
            )}
            <Count done={progress.answered} total={progress.total} />
          </p>
        </div>
        <Progress
          aria-label={candidates("progress")}
          value={
            progress.total ? (progress.answered / progress.total) * 100 : 0
          }
        />
      </div>
    </div>
  )
}
