"use client"

import { useLocale, useTranslations } from "next-intl"

import { Progress } from "@/components/ui/progress"
import { formatPercent } from "@/lib/format"
import type { Generation } from "@/types/generation"

/** How far the questions' writing has come: a bar, its percent and the topics ready. */
export function WritingProgress({
  progress,
}: {
  progress: NonNullable<Generation["progress"]>
}) {
  const t = useTranslations("generation")
  const locale = useLocale()
  const percent =
    progress.total > 0
      ? Math.min(100, Math.round((progress.done / progress.total) * 100))
      : 0

  return (
    <div className="mx-auto w-full max-w-2xl space-y-2">
      <Progress value={percent} />
      <p className="text-2xl font-light tabular-nums">
        {formatPercent(percent, locale)}
      </p>
      {progress.topics != null && (
        <p className="text-sm text-muted-foreground tabular-nums">
          {t("topicsReady", {
            ready: progress.topics_ready ?? 0,
            count: progress.topics,
          })}
        </p>
      )}
    </div>
  )
}
