"use client"

import { useTranslations } from "next-intl"

import { HistoryRow } from "@/features/billing/components/history-row"
import { VirtualList } from "@/components/common/virtual-list"
import { LIST_BOX } from "@/config/lists"
import { usePagedList } from "@/hooks/use-paged-list"
import type { CandidateLinks } from "@/lib/candidate-links"
import type { CreditHistoryEntry } from "@/types/company"

function byId(entry: CreditHistoryEntry) {
  return entry.id
}

/** Every movement of a company's credits, newest first, a page at a time; `initial` is the
 * server's first page. `api` is the company's billing routes, its own by default (the admin
 * zone's support page passes its own, and `links="support"`: its candidates open there). */
export function CreditHistory({
  companyId,
  initial,
  api = `/companies/companies/${companyId}/billing`,
  links = "company",
}: {
  companyId: string
  initial: CreditHistoryEntry[]
  api?: string
  links?: CandidateLinks
}) {
  const t = useTranslations("companyBilling")
  const { items, loadMore } = usePagedList(`${api}/history`, byId, initial)

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">{t("empty")}</p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={105}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(entry) => (
        <HistoryRow
          companyId={companyId}
          entry={entry}
          api={api}
          links={links}
        />
      )}
    />
  )
}
