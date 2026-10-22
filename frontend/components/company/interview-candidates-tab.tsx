import { CandidateList } from "@/components/company/candidate-list"
import { CandidateSearch } from "@/components/company/candidate-search"
import { ShareLink } from "@/components/company/share-link"
import type { CandidateSort } from "@/constants/interviews"
import { candidatesPath } from "@/lib/interview-page"
import type {
  Candidate,
  CandidateFilters,
  InterviewDetail,
} from "@/types/company"

/** An interview's candidates tab: its shareable link, the search, sort and status filter, and
 * the candidates, their first page from the server. */
export function InterviewCandidatesTab({
  interview,
  interviewHref,
  canEdit,
  sort,
  search,
  status,
  filters,
  candidates,
}: {
  interview: InterviewDetail
  interviewHref: string
  canEdit: boolean
  sort: CandidateSort
  search: string
  status: string | null
  filters: CandidateFilters | null
  candidates: Candidate[] | null
}) {
  return (
    <div className="space-y-6">
      <ShareLink
        interviewId={interview.id}
        linkToken={interview.link_token}
        canEdit={canEdit}
      />
      <CandidateSearch
        action={interviewHref}
        sort={sort}
        q={search}
        status={status}
        filters={filters?.filters ?? []}
      />
      <CandidateList
        path={candidatesPath(interview.id, sort, search, status)}
        interviewHref={interviewHref}
        narrowed={Boolean(search || status)}
        initial={candidates ?? []}
        canEdit={canEdit}
      />
    </div>
  )
}
