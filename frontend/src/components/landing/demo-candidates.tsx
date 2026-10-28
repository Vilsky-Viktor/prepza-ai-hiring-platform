"use client"

import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"

import { InterviewHeader } from "@/components/landing/interview-header"
import { DemoReportActions } from "@/components/landing/demo-share"
import { Badge } from "@/components/ui/badge"
import {
  DEMO_OPENED,
  DEMO_REPORT_CANDIDATES,
  DEMO_REPORT_INTERVIEW,
  type DemoCandidate,
} from "@/config/reports-demo"
import { formatPercent } from "@/lib/format"
import { gradeTone } from "@/lib/grade-tone"

/** An interview's candidates tab, small, for the landing: its header with the report's actions,
 * then each candidate's name (or email), progress, grade in the pass colours and status. The
 * opened one's row is `rowRef`, shaded while `pressed`. */
export function DemoCandidates({
  shareRef,
  sharePressed,
  rowRef,
  rowPressed,
}: {
  shareRef: React.Ref<HTMLSpanElement>
  sharePressed: boolean
  rowRef: React.Ref<HTMLLIElement>
  rowPressed: boolean
}) {
  const t = useTranslations("candidates")
  const statuses = useTranslations("candidateStatus")
  const locale = useLocale()
  const status = (candidate: DemoCandidate) => (
    <Badge variant="outline" className="h-6 px-2.5 text-sm font-light">
      {statuses(candidate.status)}
    </Badge>
  )

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex items-start justify-between gap-2">
        <InterviewHeader {...DEMO_REPORT_INTERVIEW} status="in_process" />
        <DemoReportActions shareRef={shareRef} pressed={sharePressed} />
      </div>
      <ul className="divide-y rounded-xl border">
        {DEMO_REPORT_CANDIDATES.map((candidate, index) => (
          <li
            key={candidate.email}
            ref={index === DEMO_OPENED ? rowRef : undefined}
            className={cn(
              "flex items-center justify-between gap-3 px-4 py-3 transition-colors first:rounded-t-xl last:rounded-b-xl sm:px-5",
              index === DEMO_OPENED && rowPressed && "bg-surface"
            )}
          >
            {/* On phones the status takes the email's place, under the name. */}
            <span className="min-w-0 space-y-1 sm:space-y-0">
              <span className="block truncate text-base font-medium">
                {candidate.name ?? candidate.email}
              </span>
              <span className="block truncate text-sm text-muted-foreground max-sm:hidden">
                {candidate.name ? candidate.email : "\u00a0"}
              </span>
              <span className="block sm:hidden">{status(candidate)}</span>
            </span>
            <span className="flex shrink-0 items-center gap-3 sm:gap-8">
              <span className="w-20 text-center max-sm:hidden">
                <span className="block text-xl font-light tabular-nums">
                  {formatPercent(candidate.progress, locale)}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {t("progress")}
                </span>
              </span>
              <span className="w-14 text-center sm:w-20">
                <span
                  className={cn(
                    "block text-xl font-light tabular-nums",
                    candidate.grade == null && "text-muted-foreground",
                    gradeTone(candidate.passed)
                  )}
                >
                  {formatPercent(candidate.grade, locale)}
                </span>
                <span className="block text-xs text-muted-foreground max-sm:hidden">
                  {t("grade")}
                </span>
              </span>
              <span className="flex w-26 justify-end max-sm:hidden">
                {status(candidate)}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
