"use client"

import { LayersIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { useUrlLocale } from "@/components/localized-link"
import { UseTemplate } from "@/components/templates/use-template"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { VirtualList } from "@/components/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import { hasMessage } from "@/lib/messages"
import { localizedPath } from "@/lib/locale-path"
import type { TemplateSummary } from "@/types/superadmin"
import { LIST_BOX } from "@/constants/lists"

/** The templates at `path`, newest first, a page at a time; `initial` is the server's first
 * page, and `empty` shows when there are none. A row opens the template under `openBase` (by its
 * slug with `bySlug`), and
 * for `companyId` also ends with a "Use template" button. */
export function TemplateList({
  path,
  initial,
  empty,
  openBase,
  companyId,
  bySlug,
}: {
  path: string
  initial: TemplateSummary[]
  empty: string
  openBase: string
  companyId?: string
  bySlug?: boolean
}) {
  const t = useTranslations("templates")
  const localTime = useLocalTime()
  const urlLocale = useUrlLocale()
  const { items, loadMore } = usePagedList(path, byId, initial)

  if (items.length === 0) {
    return <p className="py-16 text-center text-muted-foreground">{empty}</p>
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
        const row = (
          <>
            <span className="min-w-0 flex-1 basis-full space-y-1 sm:basis-auto">
              <span className="block text-lg font-medium break-words sm:truncate">
                {template.title}
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
            <Tooltip>
              {/* Above the row's link overlay, so hovering it shows the tooltip. */}
              <TooltipTrigger
                render={
                  <span
                    className="relative z-10 ms-auto flex w-12 shrink-0 items-center justify-end gap-1.5 text-sm text-muted-foreground tabular-nums sm:ms-0"
                    aria-label={t("topics", { count: template.topic_count })}
                  />
                }
              >
                <LayersIcon aria-hidden className="size-5" />
                {template.topic_count}
              </TooltipTrigger>
              <TooltipContent>
                {t("topics", { count: template.topic_count })}
              </TooltipContent>
            </Tooltip>
          </>
        )

        const href = `${openBase}/${(bySlug && template.slug) || template.id}`

        // One hover surface: the link stretches over the whole row, "Use template" sits on top;
        // on phones it takes its own line, at full width.
        return (
          <div className="relative flex items-center gap-6 p-6 transition-colors hover:bg-muted/50 active:bg-muted/50 max-sm:flex-wrap max-sm:gap-4">
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
