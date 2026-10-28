"use client"

import { useLocale, useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"
import { VirtualList } from "@/components/virtual-list"
import { Dot } from "@/components/dot"
import { usePagedList } from "@/hooks/use-paged-list"
import { formatPercent } from "@/lib/format"
import type { PassRate } from "@/types/superadmin"
import { LIST_BOX } from "@/constants/lists"

function rowKey(row: PassRate) {
  return row.interview_id
}

/** Company interviews with finished candidates, a page at a time in the API's order (paged by
 * key): the
 * interview and its company, how many finished, and how they did. The API marks those outside
 * the monitoring plan's triggers. */
export function PassRateList({
  path,
  initial,
}: {
  path: string
  initial: PassRate[]
}) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const percent = (value: number) => formatPercent(value, locale)
  const interviews = useTranslations("interviews")
  const { items, loadMore } = usePagedList<PassRate>(
    path,
    rowKey,
    initial,
    true
  )

  if (items.length === 0) {
    return (
      <p className="py-10 text-center text-muted-foreground">
        {t("noPassRates")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={rowKey}
      estimateSize={120}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(row) => (
        // On phones the numbers go under the title and company, on the left.
        <div className="flex items-center gap-6 p-6 max-sm:flex-col max-sm:items-stretch max-sm:gap-4 max-sm:py-8">
          <div className="min-w-0 flex-1 space-y-1">
            <p className="text-lg font-medium">
              {row.title ?? interviews("fallbackTitle")}
            </p>
            <p className="text-sm text-muted-foreground">{row.company}</p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2 text-sm text-muted-foreground tabular-nums max-sm:items-start">
            {row.outside_triggers && (
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {t("outsideTriggers")}
              </Badge>
            )}
            <span>
              {t("finished", { count: row.finished })}
              <Dot />
              {t("passed", { percent: percent(row.pass_rate) })}
            </span>
            <span>
              {t("passMark", { percent: percent(row.pass_mark) })}
              <Dot />
              {t("averageGrade", { percent: percent(row.average_grade) })}
            </span>
            {row.timeout_share !== null && (
              <span>
                {t("timedOut", { percent: percent(row.timeout_share) })}
              </span>
            )}
          </div>
        </div>
      )}
    />
  )
}
