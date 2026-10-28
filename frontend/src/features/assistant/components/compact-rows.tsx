"use client"

import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"

import type { CandidateRowData } from "@/components/common/candidate-row"
import { InterviewStatus } from "@/components/common/interview-status"
import { LocalizedLink } from "@/components/common/localized-link"
import { Badge } from "@/components/ui/badge"
import { formatPercent } from "@/lib/format"
import { gradeTone } from "@/lib/grade-tone"
import { hasMessage } from "@/lib/messages"
import { ROW_HOVER } from "@/config/lists"

type Row = { item: Record<string, unknown>; href: string | null }

// A row's cells: what it is, then its numbers and status in fixed columns, so rows line up.
const CANDIDATE_GRID =
  "grid grid-cols-[minmax(0,1fr)_3.5rem_3.5rem_5.5rem] items-center gap-3"
const INTERVIEW_GRID =
  "grid grid-cols-[minmax(0,1fr)_5.5rem_4.5rem] items-center gap-3"
const HEAD = "bg-surface px-3 py-2 text-xs text-muted-foreground"
const CELL_ROW = "px-3 py-2 text-sm"
const NUMBER = "text-end tabular-nums"

/** A row opening its page, or a plain row without one. */
function RowLink({
  href,
  onNavigate,
  className,
  children,
}: {
  href: string | null
  onNavigate: () => void
  className: string
  children: React.ReactNode
}) {
  if (!href) {
    return <div className={className}>{children}</div>
  }

  return (
    <LocalizedLink
      href={href}
      onClick={onNavigate}
      className={cn(className, ROW_HOVER)}
    >
      {children}
    </LocalizedLink>
  )
}

/** Candidates under an answer, as a compact table: name (or email) with the email under it,
 * progress, grade (green or red against the pass mark) and status; each row opens the
 * candidate's page. */
export function CandidateTable({
  rows,
  onNavigate,
}: {
  rows: Row[]
  onNavigate: () => void
}) {
  const t = useTranslations("candidates")
  const statuses = useTranslations("candidateStatus")
  const locale = useLocale()

  return (
    <div
      className="divide-y overflow-hidden rounded-xl border"
      data-testid="candidate-table"
    >
      <div className={cn(CANDIDATE_GRID, HEAD)}>
        <span>{t("name")}</span>
        <span className={NUMBER}>{t("progress")}</span>
        <span className={NUMBER}>{t("grade")}</span>
        <span />
      </div>
      {rows.map(({ item, href }, index) => {
        const candidate = item as CandidateRowData

        return (
          <RowLink
            key={index}
            href={href}
            onNavigate={onNavigate}
            className={cn(CANDIDATE_GRID, CELL_ROW)}
          >
            <span className="min-w-0">
              <span className="block truncate font-medium">
                {candidate.status === "deleted"
                  ? t("deleted")
                  : (candidate.name ?? candidate.email)}
              </span>
              {candidate.status !== "deleted" && candidate.name && (
                <span className="block truncate text-xs text-muted-foreground">
                  {candidate.email}
                </span>
              )}
            </span>
            <span className={NUMBER}>
              {formatPercent(candidate.progress, locale)}
            </span>
            <span
              className={cn(
                NUMBER,
                candidate.grade == null && "text-muted-foreground",
                gradeTone(candidate.passed)
              )}
            >
              {formatPercent(candidate.grade, locale)}
            </span>
            <span className="flex justify-end">
              <Badge
                variant={
                  candidate.status === "undelivered" ? "destructive" : "outline"
                }
                className="h-5 px-2 text-xs font-light"
              >
                {hasMessage(statuses, candidate.status)
                  ? statuses(candidate.status)
                  : candidate.status}
              </Badge>
            </span>
          </RowLink>
        )
      })}
    </div>
  )
}

/** Interviews under an answer, as a compact table: title, status and candidates; each row
 * opens the interview. */
export function InterviewTable({
  rows,
  onNavigate,
}: {
  rows: Row[]
  onNavigate: () => void
}) {
  const t = useTranslations("interviews")

  return (
    <div
      className="divide-y overflow-hidden rounded-xl border"
      data-testid="interview-table"
    >
      <div className={cn(INTERVIEW_GRID, HEAD)}>
        <span>{t("title")}</span>
        <span />
        <span className={NUMBER}>{t("candidates")}</span>
      </div>
      {rows.map(({ item, href }, index) => (
        <RowLink
          key={index}
          href={href}
          onNavigate={onNavigate}
          className={cn(INTERVIEW_GRID, CELL_ROW)}
        >
          <span className="truncate font-medium">
            {(item.title as string | null) ?? t("fallbackTitle")}
          </span>
          <span className="flex justify-end">
            {typeof item.status === "string" && (
              <InterviewStatus status={item.status} />
            )}
          </span>
          <span className={NUMBER}>
            {(item.candidate_count as number | undefined) ?? 0}
          </span>
        </RowLink>
      ))}
    </div>
  )
}
