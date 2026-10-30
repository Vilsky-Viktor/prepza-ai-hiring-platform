"use client"

import { useTranslations } from "next-intl"

import { CandidateRow } from "@/components/common/candidate-row"
import { AnswerModeIcon } from "@/features/company/components/answer-mode-icon"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import type { Candidate } from "@/types/company"
import { LIST_BOX, LIST_EMPTY } from "@/config/lists"

/** An interview's candidates, a page at a time, from `path` (the API list with its sort and
filters); `initial` is the server's first page. `narrowed` when a search or filter is on.
With `canEdit` (an owner or admin), a missing name's tooltip says they can enter it. A
candidate who takes it in another mode than the interview's (`voice`) shows that mode's icon;
the rest show none, to keep the rows calm. */
export function CandidateList({
  path,
  interviewHref,
  narrowed,
  initial,
  canEdit,
  voice,
}: {
  path: string
  interviewHref: string
  narrowed: boolean
  initial: Candidate[]
  canEdit: boolean
  // The interview's mode: taken by voice.
  voice: boolean
}) {
  const t = useTranslations("candidates")
  const { items, loadMore } = usePagedList(path, byId, initial)

  if (items.length === 0) {
    return (
      <p className={LIST_EMPTY}> {narrowed ? t("noMatches") : t("empty")}</p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={97}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(candidate) => (
        <CandidateRow
          candidate={candidate}
          href={`${interviewHref}/candidates/${candidate.id}`}
          canEdit={canEdit}
          mode={
            (candidate.voice ?? false) !== voice && (
              <AnswerModeIcon voice={!voice} />
            )
          }
        />
      )}
    />
  )
}
