"use client"

import { FlagIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { useAdminName } from "@/hooks/use-admin-name"
import { AnswerOptions } from "@/components/questions/answer-options"
import { QuestionReports } from "@/components/questions/question-reports"
import { QuestionText } from "@/components/questions/question-text"
import { ReplacementDialog } from "@/components/superadmin/replacement-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VirtualList } from "@/components/virtual-list"
import { Dot } from "@/components/dot"
import { usePagedList } from "@/hooks/use-paged-list"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { formatPercent } from "@/lib/format"
import type { QualityRow } from "@/types/superadmin"
import { LIST_BOX } from "@/config/lists"

// A row is a question as flagged now, or one revision of it as replaced.
function rowKey(row: QualityRow) {
  return row.revision_id ?? row.question_id
}

/** Questions on the quality tab, newest first, a page at a time: the question, where it is and
 * when, its flag (flagged now), and how it was doing. */
export function QualityList({
  path,
  initial,
  empty,
  byKey = false,
}: {
  path: string
  initial: QualityRow[]
  empty: string
  /** The API pages this list by key (the replaced questions). */
  byKey?: boolean
}) {
  const t = useTranslations("superadmin")
  const named = useAdminName()
  const locale = useLocale()
  const localTime = useLocalTime()
  const { items, loadMore } = usePagedList<QualityRow>(
    path,
    rowKey,
    initial,
    byKey
  )
  // Dismissed here, so gone from the list; sent to the verifier, so waiting.
  const [dismissed, setDismissed] = useState<string[]>([])
  const [sent, setSent] = useState<string[]>([])
  // Rows whose reports are open below them.
  const [openReports, setOpenReports] = useState<string[]>([])

  function reportsPath(row: QualityRow) {
    return row.revision_id
      ? `/library/superadmin/quality/revisions/${row.revision_id}/reports`
      : `/library/superadmin/quality/${row.question_id}/reports`
  }

  function toggleReports(key: string) {
    setOpenReports((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, key]
    )
  }
  const rows = items.filter((row) => !dismissed.includes(row.question_id))

  async function act(row: QualityRow, action: "fix" | "dismiss") {
    try {
      await apiFetch(
        `/library/superadmin/quality/${row.question_id}/${action}`,
        {
          method: "POST",
        }
      )

      if (action === "fix") {
        setSent((current) => [...current, row.question_id])
        toast.success(t("fixSent"))
      } else {
        setDismissed((current) => [...current, row.question_id])
      }
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    }
  }

  if (rows.length === 0) {
    return <p className="py-10 text-center text-muted-foreground">{empty}</p>
  }

  return (
    <VirtualList
      items={rows}
      getKey={rowKey}
      estimateSize={220}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(row) => (
        <div>
          {/* On phones the flag, numbers and buttons take the line under the question: the
              numbers on the left, the buttons under each other on the right. */}
          <div className="flex items-center gap-6 p-6 max-sm:flex-wrap max-sm:py-8">
            <div className="min-w-0 flex-1 space-y-4">
              {/* The question, where it is and when just under it, then its options. */}
              <div className="space-y-1">
                <QuestionText
                  text={row.text}
                  className="line-clamp-3 font-light"
                />
                <p className="text-xs text-muted-foreground">
                  <span className="normal-case">{row.set_title}</span>
                  <Dot />
                  {named("kinds", row.set_kind)}
                  <Dot />
                  <time dateTime={row.at} suppressHydrationWarning>
                    {localTime.date(row.at)}
                  </time>
                </p>
              </div>
              <AnswerOptions options={row.options} className="space-y-2" />
            </div>
            <div className="flex shrink-0 flex-col items-end gap-2 text-sm text-muted-foreground tabular-nums max-sm:grid max-sm:basis-full max-sm:grid-cols-[1fr_auto] max-sm:items-start max-sm:justify-items-start">
              {row.flag && (
                <Badge
                  variant="outline"
                  className="h-7 px-3 text-sm font-light"
                >
                  {named("flags", row.flag)}
                </Badge>
              )}
              <span>
                {t("answers", { count: row.answers })}
                {row.answers > 0 && (
                  <>
                    <Dot />
                    {t("right", {
                      percent: formatPercent(
                        (row.correct / row.answers) * 100,
                        locale
                      ),
                    })}
                  </>
                )}
              </span>
              {row.reports > 0 ? (
                <button
                  type="button"
                  aria-expanded={openReports.includes(rowKey(row))}
                  onClick={() => toggleReports(rowKey(row))}
                  className="-mx-2 -my-1 flex cursor-pointer items-center gap-1.5 rounded-lg px-2 py-1 transition-colors hover:text-foreground aria-expanded:bg-foreground/10 aria-expanded:text-foreground"
                >
                  <FlagIcon className="size-4" />
                  {t("reports", { count: row.reports })}
                </button>
              ) : (
                <span>{t("reports", { count: row.reports })}</span>
              )}
              {row.new_text && (
                // On phones on the right of the numbers, like the flagged tab's buttons.
                <span className="max-sm:col-start-2 max-sm:row-span-4 max-sm:row-start-1 max-sm:justify-self-end">
                  <ReplacementDialog
                    text={row.new_text}
                    options={row.new_options ?? []}
                  />
                </span>
              )}
              {row.actionable && (
                <span className="flex gap-2 pt-1 max-sm:col-start-2 max-sm:row-span-4 max-sm:row-start-1 max-sm:flex-col-reverse max-sm:items-end max-sm:gap-3 max-sm:justify-self-end max-sm:pt-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-3 text-sm"
                    onClick={() => act(row, "dismiss")}
                  >
                    {t("dismiss")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-sm max-sm:h-10 max-sm:px-5 max-sm:text-base"
                    disabled={sent.includes(row.question_id)}
                    onClick={() => act(row, "fix")}
                  >
                    {sent.includes(row.question_id) ? t("fixing") : t("fixNow")}
                  </Button>
                </span>
              )}
            </div>
          </div>
          {openReports.includes(rowKey(row)) && (
            <div className="bg-surface px-6 py-5">
              <QuestionReports path={reportsPath(row)} />
            </div>
          )}
        </div>
      )}
    />
  )
}
