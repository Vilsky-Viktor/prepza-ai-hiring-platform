"use client"

import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { Button } from "@/components/ui/button"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import { hasMessage } from "@/lib/messages"
import type { QuestionReport } from "@/types/feedback"

/** A question's reports in their own scroll box, loading more as the user scrolls it. */
export function QuestionReports({ path }: { path: string }) {
  const t = useTranslations("questions")
  const common = useTranslations("common")
  const reasons = useTranslations("reportReasons")
  const localTime = useLocalTime()
  const { items, loaded, failed, retry, loadMore } =
    usePagedList<QuestionReport>(path, byId)

  if (failed) {
    return (
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <p>{common("failed")}</p>
        <Button variant="outline" className="h-8 px-3 text-sm" onClick={retry}>
          {common("retry")}
        </Button>
      </div>
    )
  }

  if (!loaded) {
    return <p className="text-sm text-muted-foreground">{common("loading")}</p>
  }

  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{t("noReports")}</p>
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={52}
      onEndReached={loadMore}
      scrollClassName="max-h-64 overflow-y-auto"
      renderItem={(report) => (
        <div className="space-y-1 pb-3 text-sm">
          <p className="flex flex-wrap items-baseline justify-between gap-2">
            <span className="font-medium">
              {hasMessage(reasons, report.reason)
                ? reasons(report.reason)
                : report.reason}
            </span>
            <time
              dateTime={report.created_at}
              className="text-muted-foreground"
            >
              {localTime.date(report.created_at)}
            </time>
          </p>
          {report.comment && (
            <p className="font-light whitespace-pre-line text-muted-foreground">
              {report.comment}
            </p>
          )}
        </div>
      )}
    />
  )
}
