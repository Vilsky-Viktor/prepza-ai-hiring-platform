"use client"

import { CheckCheckIcon, CheckIcon, LayersIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"
import { cn } from "cn"

import { useLocalTime } from "@/hooks/use-local-time"
import { useUrlLocale } from "@/components/common/localized-link"
import { UseTemplate } from "@/components/templates/use-template"
import { IconStat } from "@/components/common/icon-stat"
import { Badge } from "@/components/ui/badge"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { gradeTone } from "@/lib/grade-tone"
import { byId } from "@/lib/paged-list"
import { hasMessage } from "@/lib/messages"
import { localizedPath } from "@/lib/locale-path"
import type { PracticeStatus } from "@/types/round"
import type { TemplateSummary } from "@/types/superadmin"
import { LIST_BOX, LIST_EMPTY, ROW_HOVER } from "@/config/lists"

/** The templates at `path`, newest first, a page at a time; `initial` is the server's first
 * page, and `empty` shows when there are none. A row opens the template under `openBase` (by its
 * slug with `bySlug`), and
 * for `companyId` also ends with a "Use template" button. A template in `statuses` shows the
 * signed-in talent's progress on it after its title: a check while in progress, a double check
 * in the results' green once completed, each named in its tooltip. */
export function TemplateList({
  path,
  initial,
  empty,
  openBase,
  companyId,
  bySlug,
  statuses,
}: {
  path: string
  initial: TemplateSummary[]
  empty: string
  openBase: string
  companyId?: string
  bySlug?: boolean
  statuses?: PracticeStatus[]
}) {
  const t = useTranslations("templates")
  const localTime = useLocalTime()
  const urlLocale = useUrlLocale()
  const { items, loadMore } = usePagedList(path, byId, initial)
  const practiced = new Map(
    (statuses ?? []).map((status) => [status.template_id, status])
  )

  if (items.length === 0) {
    return <p className={LIST_EMPTY}>{empty}</p>
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={89}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(template) => {
        const level = `levels.${template.level}` as const
        const practice = practiced.get(template.id)
        const row = (
          <>
            <span className="min-w-0 flex-1 basis-full space-y-1 sm:basis-auto">
              {/* On phones the title wraps and its mark follows its last word; from sm up, the
                  title truncates and the mark stays beside it. */}
              <span className="block text-lg font-medium break-words sm:flex sm:items-center sm:gap-2">
                <span className="sm:min-w-0 sm:truncate">{template.title}</span>
                {practice &&
                  (practice.status === "completed" ? (
                    <IconStat
                      label={t("completed", {
                        done: practice.topics_done,
                        total: practice.topics_total,
                      })}
                      icon={<CheckCheckIcon aria-hidden className="size-5" />}
                      className={cn(
                        gradeTone(true),
                        "ms-1 hover:text-current sm:-ms-1"
                      )}
                      data-status={practice.status}
                    />
                  ) : (
                    <IconStat
                      label={t("inProgress", {
                        done: practice.topics_done,
                        total: practice.topics_total,
                      })}
                      icon={<CheckIcon aria-hidden className="size-5" />}
                      className="ms-1 text-primary hover:text-primary sm:-ms-1"
                      data-status={practice.status}
                    />
                  ))}
              </span>
              <span className="block text-sm text-muted-foreground">
                <time dateTime={template.created_at} suppressHydrationWarning>
                  {localTime.date(template.created_at)}
                </time>
              </span>
            </span>
            {/* Their own column, so the tags line up whatever the title's length. */}
            <span className="flex shrink-0 gap-2">
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {hasMessage(t, level) ? t(level) : template.level}
              </Badge>
              <Badge
                variant="outline"
                className="h-7 px-3 text-sm font-light uppercase"
              >
                {template.language}
              </Badge>
            </span>
            {/* A fixed column on every row; the hover background only around the icon and count. */}
            <span className="ms-auto flex w-12 shrink-0 justify-end sm:-ms-2">
              <IconStat
                label={t("topics", { count: template.topic_count })}
                icon={<LayersIcon aria-hidden className="size-5" />}
                className="text-sm"
              >
                {template.topic_count}
              </IconStat>
            </span>
          </>
        )

        const href = `${openBase}/${(bySlug && template.slug) || template.id}`

        // One hover surface: the link stretches over the whole row, "Use template" sits on top;
        // on phones it takes its own line, at full width.
        return (
          <div
            className={`relative flex items-center gap-6 p-6 ${ROW_HOVER} max-sm:flex-wrap max-sm:gap-4`}
          >
            <Link
              // On a language's address (/de/tests), a template in that language opens there
              // too; the others have only their English address.
              href={
                template.language === urlLocale
                  ? localizedPath(urlLocale, href)
                  : href
              }
              // On phones the title takes its own line, the tags and count the next.
              className="flex min-w-0 flex-1 flex-wrap items-center gap-x-6 gap-y-3 after:absolute after:inset-0 sm:flex-nowrap"
            >
              {row}
            </Link>
            {companyId && (
              <div className="relative z-10 max-sm:basis-full max-sm:*:w-full">
                <UseTemplate templateId={template.id} companyId={companyId} />
              </div>
            )}
          </div>
        )
      }}
    />
  )
}
