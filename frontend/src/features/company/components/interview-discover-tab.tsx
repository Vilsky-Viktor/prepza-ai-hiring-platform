"use client"

import { useTranslations } from "next-intl"

import { DiscoverRow } from "@/features/company/components/discover-row"
import { VirtualList } from "@/components/common/virtual-list"
import { InfoCard } from "@/components/common/warning-card"
import { LIST_BOX, LIST_EMPTY } from "@/config/lists"
import { usePagedList } from "@/hooks/use-paged-list"
import { discoverPath } from "@/lib/interview-discover"
import type { DiscoverPerson } from "@/types/company"

/** An interview's Discover tab: what it lists (an info card), then the people open to offers whose practice
 * matches the interview, a page at a time, in the order the API gives (who practised last
 * first); `initial` is the server's first page. */
export function InterviewDiscoverTab({
  interviewId,
  canEdit,
  initial,
}: {
  interviewId: string
  canEdit: boolean
  // Null when the server couldn't load it: the list then loads here.
  initial: DiscoverPerson[] | null
}) {
  const t = useTranslations("interviews")
  const path = discoverPath(interviewId)
  const { items, loadMore } = usePagedList(
    path,
    (person: DiscoverPerson) => person.id,
    initial ?? undefined
  )

  return (
    <div className="space-y-6">
      <InfoCard className="max-sm:-mx-6 max-sm:rounded-none">
        {t("discoverText")}
      </InfoCard>
      {items.length === 0 ? (
        <p className={LIST_EMPTY}>{t("discoverEmpty")}</p>
      ) : (
        <VirtualList
          items={items}
          getKey={(person) => person.id}
          estimateSize={140}
          onEndReached={loadMore}
          className={LIST_BOX}
          renderItem={(person) => (
            <DiscoverRow
              person={person}
              invitePath={`${path}/${encodeURIComponent(person.id)}/invite`}
              canEdit={canEdit}
            />
          )}
        />
      )}
    </div>
  )
}
