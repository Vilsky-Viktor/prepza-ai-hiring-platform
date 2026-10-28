"use client"

import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { VirtualList } from "@/components/virtual-list"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { usePagedList } from "@/hooks/use-paged-list"
import type { PracticeRoundSummary } from "@/types/round"
import { formatPercent } from "@/lib/format"

function byRound(round: PracticeRoundSummary) {
  return round.round_id
}

/** A talent's rounds on one practice test, newest first, a page at a time, with their
 * progress and grades; each opens its results. `initial` is the server's first page. */
export function PracticeRoundList({
  templateId,
  initial,
}: {
  templateId: string
  initial: PracticeRoundSummary[]
}) {
  const t = useTranslations("practice")
  const locale = useLocale()
  const localTime = useLocalTime()
  const { items, loadMore } = usePagedList(
    `/rounds/practice/${templateId}/rounds`,
    byRound,
    initial
  )

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">{t("noRounds")}</p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byRound}
      estimateSize={97}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(round) => (
        <Link
          href={`/practice/rounds/${round.round_id}`}
          className={`flex items-center justify-between gap-4 p-6 ${ROW_HOVER}`}
        >
          <time
            dateTime={round.started_at}
            className="text-lg"
            suppressHydrationWarning
          >
            {localTime.date(round.started_at)}
          </time>
          {/* Progress and grade, labelled like the candidate list's numbers. */}
          <span className="flex shrink-0 items-center gap-6 sm:gap-10">
            <span className="w-20 text-center sm:w-24">
              <span className="block text-2xl font-light tabular-nums">
                {formatPercent(round.progress, locale)}
              </span>
              <span className="block text-sm text-muted-foreground">
                {t("progressLabel")}
              </span>
            </span>
            <span className="w-20 text-center sm:w-24">
              <span
                className={
                  round.grade == null
                    ? "block text-2xl font-light text-muted-foreground"
                    : "block text-2xl font-light tabular-nums"
                }
              >
                {formatPercent(round.grade, locale)}
              </span>
              <span className="block text-sm text-muted-foreground">
                {t("gradeLabel")}
              </span>
            </span>
          </span>
        </Link>
      )}
    />
  )
}
