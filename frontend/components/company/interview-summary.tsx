"use client"

import { UsersIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { InterviewStatus } from "@/components/company/interview-status"
import { IconStat } from "@/components/icon-stat"

/** An interview's row content: its title and date, then its status (when it has one) and how
 * many candidates it has. */
export function InterviewSummary({
  title,
  createdAt,
  status,
  candidateCount,
}: {
  title: string
  createdAt: string
  status: string | null
  candidateCount: number
}) {
  const t = useTranslations("interviews")
  const localTime = useLocalTime()

  return (
    <>
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-medium">{title}</span>
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
