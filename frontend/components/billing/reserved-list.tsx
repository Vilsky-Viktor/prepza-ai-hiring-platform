"use client"

import Link from "next/link"

import { NoName } from "@/components/company/no-name"
import { VirtualList } from "@/components/virtual-list"
import { WrappedEmail } from "@/components/wrapped-email"
import { Dot } from "@/components/dot"
import { LIST_BOX, ROW_HOVER } from "@/constants/lists"
import { usePagedList } from "@/hooks/use-paged-list"
import { candidateHref, type CandidateLinks } from "@/lib/candidate-links"
import type { CreditCandidate } from "@/types/company"

function byInvite(candidate: CreditCandidate) {
  return candidate.invite_id
}

/** Candidates invited who haven't finished, whose credits are set aside, newest first; each
 * opens the candidate. `initial` is the server's first page. `api` is the company's billing
 * routes, its own by default; the admin zone's support page passes its own and
 * `links="support"`, so its candidates open there. */
export function ReservedList({
  companyId,
  initial,
  api = `/companies/companies/${companyId}/billing`,
  links = "company",
}: {
  companyId: string
  initial: CreditCandidate[]
  api?: string
  links?: CandidateLinks
}) {
  const { items, loadMore } = usePagedList(`${api}/reserved`, byInvite, initial)

  return (
    <VirtualList
      items={items}
      getKey={byInvite}
      estimateSize={105}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(candidate) => {
        const content = (
          <>
            <span className="block text-lg font-medium">
              <WrappedEmail email={candidate.email} />
            </span>
            <span className="block text-sm break-all text-muted-foreground">
              {candidate.name ?? <NoName hint="list" />}
              {candidate.interview_title && (
                <span className="normal-case">
                  <Dot />
                  {candidate.interview_title}
                </span>
              )}
            </span>
          </>
        )

        return (
          <Link
            href={candidateHref(links, companyId, candidate)}
            className={`block space-y-1 p-6 ${ROW_HOVER}`}
          >
            {content}
          </Link>
        )
      }}
    />
  )
}
