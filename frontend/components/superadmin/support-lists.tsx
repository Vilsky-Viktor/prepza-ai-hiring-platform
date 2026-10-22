"use client"

import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"

import { VirtualList } from "@/components/virtual-list"
import { WrappedEmail } from "@/components/wrapped-email"
import { Dotted } from "@/components/dot"
import { LIST_BOX } from "@/constants/lists"
import { useLocalTime } from "@/hooks/use-local-time"
import { usePagedList } from "@/hooks/use-paged-list"
import { formatPercent } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import type { Interview } from "@/types/company"
import type { SupportCandidateRow } from "@/types/superadmin"

function byId(item: { id: string }) {
  return item.id
}

/** A company's interviews on its support page, newest first, a page at a time: each one's
 * status, when it was made and how many candidates it has; each opens its support page. */
export function SupportInterviews({
  api,
  initial,
}: {
  api: string
  initial: Interview[]
}) {
  const t = useTranslations("superadmin")
  const statuses = useTranslations("interviewStatus")
  const localTime = useLocalTime()
  const { items, loadMore } = usePagedList(`${api}/interviews`, byId, initial)

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {t("supportNoInterviews")}
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
        <Link
          href={`/superadmin/support/interviews/${interview.id}`}
          className="block space-y-1 p-6 transition-colors hover:bg-muted/50 active:bg-muted/50"
        >
          <p className="text-lg font-medium break-words normal-case">
            {interview.title ?? t("supportUntitled")}
          </p>
          <p className="text-sm text-muted-foreground">
            <Dotted
              items={[
                hasMessage(statuses, interview.status)
                  ? statuses(interview.status)
                  : interview.status,
                localTime.date(interview.created_at),
                t("supportCandidates", { count: interview.candidate_count }),
              ]}
            />
          </p>
        </Link>
      )}
    />
  )
}

function byInvite(candidate: SupportCandidateRow) {
  return candidate.invite_id
}

/** An interview's candidates on its support page, newest first, a page at a time: each one's
 * email, name, status and grade; each opens their support page. */
export function SupportInterviewCandidates({
  api,
  initial,
}: {
  api: string
  initial: SupportCandidateRow[]
}) {
  const t = useTranslations("superadmin")
  const statuses = useTranslations("candidateStatus")
  const locale = useLocale()
  const { items, loadMore } = usePagedList(
    `${api}/candidates`,
    byInvite,
    initial
  )

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {t("supportNoCandidates")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byInvite}
      estimateSize={89}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(candidate) => (
        <Link
          href={`/superadmin/support/candidates/${candidate.invite_id}`}
          className="flex items-center justify-between gap-4 p-6 transition-colors hover:bg-muted/50 active:bg-muted/50"
        >
          <span className="min-w-0 space-y-1">
            <span className="block text-lg font-medium">
              <WrappedEmail email={candidate.email} />
            </span>
            <span className="block text-sm text-muted-foreground">
              <Dotted
                items={[
                  candidate.name,
                  hasMessage(statuses, candidate.status)
                    ? statuses(candidate.status)
                    : candidate.status,
                ]}
              />
            </span>
          </span>
          {candidate.grade != null && (
            <span className="shrink-0 font-heading text-xl font-medium tabular-nums">
              {formatPercent(candidate.grade, locale)}
            </span>
          )}
        </Link>
      )}
    />
  )
}
