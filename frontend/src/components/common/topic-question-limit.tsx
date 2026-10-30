"use client"

import { UserIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { IconStat } from "@/components/common/icon-stat"
import { QuestionMarkIcon } from "@/components/icons/question-mark-icon"
import { TopicLimit } from "@/components/common/topic-limit"

/** A topic's question count, in one short line under its "manage questions" button: how many
 * each candidate gets (editable with `limitPath`) of how many the topic has; just the count
 * when there's no limit. `field` shows in the editable number's place (the landing's picture). */
export function TopicQuestionLimit({
  count,
  limit,
  limitPath,
  field,
}: {
  count: number
  limit: number | null
  limitPath?: string
  field?: ReactNode
}) {
  const t = useTranslations("questions")

  if (!limitPath && !field && limit == null) {
    return (
      <p className="shrink-0 text-sm whitespace-nowrap text-muted-foreground tabular-nums">
        {count} {t("count", { count })}
      </p>
    )
  }

  return (
    <p className="flex shrink-0 items-center gap-2 text-sm whitespace-nowrap text-muted-foreground tabular-nums">
      {field ??
        (limitPath ? (
          // Remounts with the saved value after each change.
          <TopicLimit
            key={limit ?? "all"}
            path={limitPath}
            count={count}
            limit={limit}
          />
        ) : (
          <span className="text-foreground">{limit}</span>
        ))}
      <span className="flex items-center gap-1.5">
        {/* "of 100 ? per 👤": icons stand for questions and candidate, named in tooltips. */}
        {t("ofCount", { count })}
        <IconStat
          label={t("count", { count })}
          icon={<QuestionMarkIcon aria-hidden className="h-4 w-2" />}
        />
        {t("per")}
        <IconStat
          label={t("candidate")}
          icon={<UserIcon aria-hidden className="size-4" />}
        />
      </span>
    </p>
  )
}
