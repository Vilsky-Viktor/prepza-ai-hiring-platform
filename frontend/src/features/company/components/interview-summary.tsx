"use client"

import { UsersIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { InterviewStatus } from "@/components/common/interview-status"
import { IconStat } from "@/components/common/icon-stat"
import { PinnedNote } from "@/components/common/pinned-note"

/** An interview's row content: its title, its pinned note and date, then its status (when it
 * has one) and how many candidates it has. */
export function InterviewSummary({
  title,
  createdAt,
  status,
  candidateCount,
  pinnedNote,
}: {
  title: string
  createdAt: string
  status: string | null
  candidateCount: number
  pinnedNote?: string | null
}) {
  const t = useTranslations("interviews")
  const localTime = useLocalTime()

  return (
    <>
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-medium">{title}</span>
        {pinnedNote && <PinnedNote text={pinnedNote} className="text-sm" />}
        <span className="block text-sm text-muted-foreground">
          <time dateTime={createdAt} suppressHydrationWarning>
            {localTime.date(createdAt)}
          </time>
        </span>
      </span>
      <span
        data-slot="interview-stats"
        className="flex shrink-0 items-center gap-6"
      >
        {status && <InterviewStatus status={status} />}
        {/* The same 3rem column on every row; the hover background only around the icon and count. */}
        <span className="flex w-12 shrink-0 justify-end">
          <IconStat
            label={t("candidateCount", { count: candidateCount })}
            icon={<UsersIcon aria-hidden className="size-5" />}
            className="text-sm"
            data-testid="candidate-count"
          >
            {candidateCount}
          </IconStat>
        </span>
      </span>
    </>
  )
}
