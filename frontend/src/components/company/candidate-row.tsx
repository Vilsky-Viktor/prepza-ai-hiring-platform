"use client"

import { cn } from "cn"
import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { CandidateSignals } from "@/components/company/candidate-signals"
import { NoName } from "@/components/company/no-name"
import { Badge } from "@/components/ui/badge"
import { WrappedEmail } from "@/components/wrapped-email"
import { gradeTone } from "@/lib/grade-tone"
import type { Candidate } from "@/types/company"
import { formatPercent } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { ROW_HOVER } from "@/config/lists"

// What a row shows; the assistant's answers may leave out the date or the progress.
export type CandidateRowData = Pick<
  Candidate,
  | "email"
  | "name"
  | "status"
  | "grade"
  | "passed"
  | "tab_leaves"
  | "copies"
  | "fast_answers"
> & { created_at?: string; progress?: number }

/** One candidate in a list: email, name ("no name yet" until known), date and integrity signals, progress, grade and status,
 * opening `href`. Side by side when its list is wide enough, stacked in a narrow one (the
 * assistant's panel). */
export function CandidateRow({
  candidate,
  href,
  onClick,
  canEdit = false,
}: {
  candidate: CandidateRowData
  href: string
  onClick?: () => void
  // An owner or admin, who can enter a missing name on the candidate's page.
  canEdit?: boolean
}) {
  const t = useTranslations("candidates")
  const locale = useLocale()
  const statuses = useTranslations("candidateStatus")
  const localTime = useLocalTime()

  return (
    <Link
      href={href}
      onClick={onClick}
      className={`@container block ${ROW_HOVER}`}
    >
      <span className="flex flex-col gap-4 p-4 @xl:flex-row @xl:items-center @xl:justify-between @xl:p-6">
        <span className="min-w-0 space-y-1">
          <span className="block">
            <span className="block text-lg font-medium">
              {candidate.status === "deleted" ? (
                t("deleted")
              ) : (
                <WrappedEmail email={candidate.email} />
              )}
            </span>
            {candidate.status !== "deleted" && (
              <span className="block text-sm leading-tight break-all text-muted-foreground">
                {candidate.name ?? <NoName hint={canEdit ? "list" : "view"} />}
              </span>
            )}
          </span>
          <span className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            {candidate.created_at && (
              <time dateTime={candidate.created_at} suppressHydrationWarning>
                {localTime.date(candidate.created_at)}
              </time>
            )}
            <CandidateSignals candidate={candidate} />
          </span>
        </span>
        {/* Progress, grade and status: centered on their own line in a narrow row. */}
        <span className="flex shrink-0 items-center justify-center gap-6 @xl:justify-normal @xl:gap-10">
          <span className="w-20 text-center @xl:w-24">
            <span className="block text-2xl font-light tabular-nums">
              {formatPercent(candidate.progress, locale)}
            </span>
            <span className="block text-sm text-muted-foreground">
              {t("progress")}
            </span>
          </span>
          <span className="w-20 text-center @xl:w-24">
            <span
              className={cn(
                "block text-2xl font-light tabular-nums",
                candidate.grade == null && "text-muted-foreground",
                gradeTone(candidate.passed)
              )}
            >
              {formatPercent(candidate.grade, locale)}
            </span>
            <span className="block text-sm text-muted-foreground">
              {t("grade")}
            </span>
          </span>
          <span className="flex justify-end @xl:w-32">
            <Badge
              variant={
                candidate.status === "undelivered" ? "destructive" : "outline"
              }
              className="h-7 px-3 text-sm font-light"
            >
              {hasMessage(statuses, candidate.status)
                ? statuses(candidate.status)
                : candidate.status}
            </Badge>
          </span>
        </span>
      </span>
    </Link>
  )
}
