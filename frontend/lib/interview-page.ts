import { CANDIDATE_SORTS, type CandidateSort } from "@/constants/interviews"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import type {
  Candidate,
  CandidateFilters,
  InterviewDetail,
  InviteLimits,
} from "@/types/company"

/** What an interview's page asks for in its address: its tab, and the candidates' sort, search
 * and status. */
export type InterviewQuery = {
  tab?: string
  sort?: string
  q?: string
  status?: string
  ready?: string
}

/** The candidates' first page, with its sort, search and status (the API checks the status). */
export function candidatesPath(
  id: string,
  sort: CandidateSort,
  search: string,
  status: string | null
) {
  const query = new URLSearchParams({ sort })

  if (search) {
    query.set("q", search)
  }

  if (status) {
    query.set("status", status)
  }

  return `/companies/interviews/${id}/candidates?${query}`
}

/** Everything an interview's page shows, fetched together, the candidates only for their tab:
 * their first page renders on the server, the rest load as the user scrolls. A sort or status
 * the API doesn't offer is ignored. */
export async function loadInterviewPage(id: string, query: InterviewQuery) {
  const sort =
    CANDIDATE_SORTS.find((option) => option === query.sort) ??
    CANDIDATE_SORTS[0]
  const search = query.q?.trim() ?? ""
  const shownCandidates = query.tab === "candidates"
  const firstPath = candidatesPath(id, sort, search, query.status ?? null)
  const [interview, filters, firstPage, limits] = await Promise.all([
    serverFetch<InterviewDetail>(`/companies/interviews/${id}`),
    shownCandidates
      ? serverFetch<CandidateFilters>(
          "/companies/interviews/candidates/filters"
        )
      : null,
    shownCandidates
      ? serverFetch<Candidate[]>(`${firstPath}&limit=${PAGE_SIZE}`)
      : null,
    // The invite dialog's texts quote the current limit.
    serverFetch<InviteLimits>("/companies/limits"),
  ])
  const status =
    filters?.filters.find((option) => option === query.status) ?? null
  const candidates =
    query.status && !status
      ? await serverFetch<Candidate[]>(
          `${candidatesPath(id, sort, search, null)}&limit=${PAGE_SIZE}`
        )
      : firstPage

  return { interview, filters, candidates, limits, sort, search, status }
}

/** An interview page's tab. */
export type InterviewTab = "topics" | "candidates" | "settings"

/** The tab shown: the one asked for once the interview is ready (settings only for those who
 * can edit), else its topics. */
export function interviewTab(
  tab: string | undefined,
  ready: boolean,
  canEdit: boolean
): InterviewTab {
  return ready && (tab === "candidates" || (tab === "settings" && canEdit))
    ? tab
    : "topics"
}
