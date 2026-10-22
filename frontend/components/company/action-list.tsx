"use client"

import { useFormatter, useTranslations } from "next-intl"

import { Dot, Dotted } from "@/components/dot"
import { VirtualList } from "@/components/virtual-list"
import { LIST_BOX } from "@/constants/lists"
import { useLocalTime } from "@/hooks/use-local-time"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import { hasMessage } from "@/lib/messages"
import type { CompanyAction } from "@/types/company"

/** A company's action log from `path` (the API list with its filters), newest first, loading
 * more as it scrolls; `initial` is the server's first page, if it rendered one. Each row: what a
 * member did and about what, then who, when to the minute, and through what (the assistant, an
 * AI app, the API or an ATS). The owner's tab and the admin zone's support page show the same
 * rows. `narrowed` when a filter is on. */
export function ActionList({
  path,
  initial,
  narrowed = false,
}: {
  path: string
  initial?: CompanyAction[]
  narrowed?: boolean
}) {
  const t = useTranslations("actionLog")
  const format = useFormatter()
  const localTime = useLocalTime()
  const { items, loaded, loadMore } = usePagedList(path, byId, initial)

  // A person who's gone (people are never kept in the log) reads as such.
  function target(action: CompanyAction) {
    if (action.target) {
      return action.target
    }

    if (action.target_kind === "candidate") {
      return t("deletedCandidate")
    }

    return action.target_kind === "member" ? t("formerMember") : null
  }

  // A value from the API by its name in `group`, or as it is when the log has no name for it.
  function named(group: "actions" | "permissions" | "via", value: string) {
    const key = `${group}.${value}` as const

    return hasMessage(t, key) ? t(key) : value
  }

  if (!loaded) {
    return null
  }

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {narrowed ? t("noMatches") : t("empty")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={89}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(action) => (
        <div className="space-y-1 p-6">
          <p className="text-lg font-medium">
            {named("actions", action.action)}
            {target(action) && (
              <span className="font-normal break-words normal-case">
                <Dot />
                {target(action)}
              </span>
            )}
            {action.removed && action.removed.length > 0 && (
              <span className="font-normal normal-case">
                <Dot />
                {t("removed", {
                  permissions: format.list(
                    action.removed.map((item) => named("permissions", item))
                  ),
                })}
              </span>
            )}
          </p>
          <p className="text-sm break-words text-muted-foreground">
            <Dotted
              items={[
                action.user_email ?? t("formerMember"),
                localTime.dateTime(action.created_at),
                action.via && named("via", action.via),
              ]}
            />
          </p>
        </div>
      )}
    />
  )
}
