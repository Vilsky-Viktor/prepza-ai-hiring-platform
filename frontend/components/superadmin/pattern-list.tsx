"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { useAdminName } from "@/hooks/use-admin-name"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VirtualList } from "@/components/virtual-list"
import { Dot } from "@/components/dot"
import { usePagedList } from "@/hooks/use-paged-list"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { QualityPattern } from "@/types/generation"
import { LIST_BOX } from "@/constants/lists"

function rowKey(row: QualityPattern) {
  return row.id
}

/** Patterns of one status, a page at a time, most recently seen first: the rule, the flag of
 * the questions it comes from, how many showed it, and when it was first and last seen. A
 * proposed one is approved or dismissed here, and leaves the list. */
export function PatternList({
  path,
  initial,
}: {
  path: string
  initial: QualityPattern[]
}) {
  const t = useTranslations("superadmin")
  const named = useAdminName()
  const localTime = useLocalTime()
  const { items, loadMore } = usePagedList<QualityPattern>(
    path,
    rowKey,
    initial
  )
  // Approved or dismissed here, so gone from this status's list.
  const [reviewed, setReviewed] = useState<string[]>([])
  const rows = items.filter((row) => !reviewed.includes(row.id))

  async function review(row: QualityPattern, action: "approve" | "dismiss") {
    try {
      await apiFetch(`/generate/superadmin/patterns/${row.id}/${action}`, {
        method: "POST",
      })
      setReviewed((current) => [...current, row.id])
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    }
  }

  if (rows.length === 0) {
    return (
      <p className="py-10 text-center text-muted-foreground">
        {t("noPatterns")}
      </p>
    )
  }

  return (
    <VirtualList
      items={rows}
      getKey={rowKey}
      estimateSize={120}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(row) => (
        // On phones the flag, numbers and buttons go under the rule, the buttons on a line of
        // their own.
        <div
          className="flex items-center gap-6 p-6 max-sm:flex-col max-sm:items-stretch max-sm:gap-4 max-sm:py-8"
          data-testid="pattern-row"
        >
          <div className="min-w-0 flex-1 space-y-1">
            <p className="font-light normal-case">{row.text}</p>
            <p className="text-xs text-muted-foreground">
              {t.rich("firstSeen", localTime.dateValues(row.first_seen))}
              <Dot />
              {t.rich("lastSeen", localTime.dateValues(row.last_seen))}
            </p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2 text-sm text-muted-foreground tabular-nums max-sm:items-start">
            {/* On phones the problem and the count share a line, the buttons on the right. */}
            <span className="flex flex-col items-end gap-2 max-sm:flex-row max-sm:items-center max-sm:gap-3">
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {named("flags", row.flag)}
              </Badge>
              <span>
                {t("patternQuestions", { count: row.question_count })}
              </span>
            </span>
            {row.status === "proposed" && (
              <span className="flex gap-2 pt-1 max-sm:self-end max-sm:pt-0">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 px-3 text-sm max-sm:h-10 max-sm:px-5 max-sm:text-base"
                  onClick={() => review(row, "dismiss")}
                >
                  {t("dismiss")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 px-3 text-sm max-sm:h-10 max-sm:px-5 max-sm:text-base"
                  onClick={() => review(row, "approve")}
                >
                  {t("approve")}
                </Button>
              </span>
            )}
          </div>
        </div>
      )}
    />
  )
}
