"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"

import { DeleteInterview } from "@/features/company/components/delete-interview"
import { InterviewSummary } from "@/features/company/components/interview-summary"
import { TryInterview } from "@/features/company/components/try-interview"
import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { byId } from "@/lib/paged-list"
import type { Interview } from "@/types/company"
import { LIST_BOX, LIST_EMPTY, ROW_HOVER } from "@/config/lists"

/** A company's interviews at `path` (narrowed by a search when `searched`), newest first, a page
 * at a time; `initial` is the server's first page. */
export function InterviewList({
  companyId,
  path,
  initial,
  canEdit,
  searched,
}: {
  companyId: string
  path: string
  initial: Interview[]
  // Viewers preview a test but don't delete it.
  canEdit: boolean
  searched: boolean
}) {
  const t = useTranslations("interviews")
  const { items, setItems, loadMore } = usePagedList(path, byId, initial)

  if (items.length === 0) {
    return (
      <p
        data-testid={searched ? "no-matches" : "no-interviews"}
        className={LIST_EMPTY}
      >
        {searched ? t("noMatches") : t("empty")}
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
      renderItem={(interview) => (
        // One hover surface: the link stretches over the whole row, Delete sits on top of it.
        // Phones show the title and date, without the status, counts and preview button.
        <div
          className={`relative flex items-center gap-2 p-6 pe-3 ${ROW_HOVER}`}
        >
          <Link
            href={`/companies/${companyId}/interviews/${interview.id}`}
            data-testid={
              interview.generation_failed ? "generation-failed" : undefined
            }
            className="flex min-w-0 flex-1 items-center justify-between gap-4 after:absolute after:inset-0 max-sm:[&_[data-slot=interview-stats]]:hidden"
          >
            <InterviewSummary
              title={
                interview.title ??
                (interview.generation_failed
                  ? t("generationFailed")
                  : t("generating"))
              }
              createdAt={interview.created_at}
              // Still generating: no status yet.
              status={interview.set_id ? interview.status : null}
              candidateCount={interview.candidate_count}
              pinnedNote={interview.pinned_note}
              voice={interview.voice ?? false}
            />
          </Link>
          {/* Still generating: cancelling it, on its page, is the way to remove it. */}
          {interview.set_id && (
            <div className="relative z-10 flex">
              <TryInterview
                companyId={companyId}
                interviewId={interview.id}
                title={interview.title ?? t("fallbackTitle")}
                className="max-sm:hidden"
              />
              {canEdit && (
                <DeleteInterview
                  interviewId={interview.id}
                  title={interview.title ?? t("fallbackTitle")}
                  onRemoved={() =>
                    setItems((current) =>
                      current.filter((item) => item.id !== interview.id)
                    )
                  }
                />
              )}
            </div>
          )}
        </div>
      )}
    />
  )
}
