import Link from "next/link"
import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { CandidateList } from "@/components/company/candidate-list"
import { CandidateSearch } from "@/components/company/candidate-search"
import { DeleteInterview } from "@/components/company/delete-interview"
import { InterviewNav } from "@/components/company/interview-nav"
import { InterviewReportActions } from "@/components/company/interview-report-actions"
import { TryInterview } from "@/components/company/try-interview"
import { EditableTitle } from "@/components/editable-title"
import { EntityId } from "@/components/entity-id"
import { InterviewEstimate } from "@/components/company/interview-estimate"
import { InterviewSettings } from "@/components/company/interview-settings"
import { InterviewTopics } from "@/components/company/interview-topics"
import { InterviewStatus } from "@/components/company/interview-status"
import { InviteCandidate } from "@/components/company/invite-candidate"
import { WhatsNext } from "@/components/company/whats-next"
import { ShareLink } from "@/components/company/share-link"
import { PageHeader } from "@/components/page-header"
import { SignInPage } from "@/components/sign-in-page"
import { Button } from "@/components/ui/button"
import { CANDIDATE_SORTS, READY_PARAM } from "@/constants/interviews"
import { PAGE_SIZE } from "@/constants/lists"
import { INTERVIEW_TAB_HELP } from "@/constants/page-help"
import { serverFetch, signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type {
  Candidate,
  CandidateFilters,
  InterviewDetail,
  InviteLimits,
} from "@/types/company"

export const generateMetadata = () => translatedTitle("interviews", "interview")

export default async function InterviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string; id: string }>
  searchParams: Promise<{
    tab?: string
    sort?: string
    q?: string
    status?: string
    ready?: string
  }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId, id } = await params
  const query = await searchParams
  const { tab, sort: asked, q, status: askedStatus } = query
  const sort =
    CANDIDATE_SORTS.find((option) => option === asked) ?? CANDIDATE_SORTS[0]
  const t = await getTranslations("interviews")
  const search = q?.trim() ?? ""
  const shownCandidates = tab === "candidates"

  // The candidates' first page, with its sort, search and status (the API checks the status).
  function candidatesPath(status: string | null) {
    const query = new URLSearchParams({ sort })

    if (search) {
      query.set("q", search)
    }

    if (status) {
      query.set("status", status)
    }

    return `/companies/interviews/${id}/candidates?${query}`
  }

  // Fetched together, and the candidates only for their tab. Their first page renders on the
  // server; the rest load as the user scrolls.
  const [interview, filters, firstPage, limits] = await Promise.all([
    serverFetch<InterviewDetail>(`/companies/interviews/${id}`),
    shownCandidates
      ? serverFetch<CandidateFilters>(
          "/companies/interviews/candidates/filters"
        )
      : null,
    shownCandidates
      ? serverFetch<Candidate[]>(
          `${candidatesPath(askedStatus ?? null)}&limit=${PAGE_SIZE}`
        )
      : null,
    // The invite dialog's texts quote the current limit.
    serverFetch<InviteLimits>("/companies/limits"),
  ])
  // Only what the API offers; anything else in the address is ignored.
  const status =
    filters?.filters.find((option) => option === askedStatus) ?? null
  const candidates =
    askedStatus && !status
      ? await serverFetch<Candidate[]>(
          `${candidatesPath(null)}&limit=${PAGE_SIZE}`
        )
      : firstPage

  if (!interview) {
    notFound()
  }

  const interviewsHref = `/companies/${companyId}/interviews`
  const interviewHref = `${interviewsHref}/${id}`
  const ready = Boolean(interview.set_id)
  // Viewers see everything but change nothing.
  const canEdit = interview.can_edit
  const current =
    ready && (tab === "candidates" || (tab === "settings" && canEdit))
      ? tab
      : "topics"

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      {/* Just generated: what to do next, for those who can do it. */}
      {ready && canEdit && query[READY_PARAM] && (
        <WhatsNext
          title={interview.title ?? t("fallbackTitle")}
          interviewHref={interviewHref}
        />
      )}
      <div className="space-y-6">
        <PageHeader
          back={
            <BackLink href={interviewsHref} help={INTERVIEW_TAB_HELP[current]}>
              {t("title")}
            </BackLink>
          }
          title={
            <div className="flex items-start justify-between gap-4 max-sm:flex-wrap">
              <div className="min-w-0 flex-1">
                {interview.title ? (
                  <EditableTitle
                    title={interview.title}
                    path={`/companies/interviews/${interview.id}/title`}
                    editable={canEdit}
                  />
                ) : (
                  <h1
                    className="font-heading text-3xl font-medium tracking-tight text-balance"
                    data-testid={
                      interview.generation_failed
                        ? "generation-failed"
                        : undefined
                    }
                  >
                    {interview.generation_failed
                      ? t("generationFailed")
                      : t("generating")}
                  </h1>
                )}
                {/* The status under the title, before the buttons on phones, and the id to
                    quote when writing to prepza (also while generating, or after a failure). */}
                <div className="mt-1 flex flex-wrap items-center gap-x-4">
                  {ready && <InterviewStatus status={interview.status} />}
                  <EntityId id={interview.id} />
                </div>
              </div>
              {/* The test's own actions sit on its tab; inviting, on the candidates tab. The
                  buttons overhang the title's line, so the row is as tall as the title on every
                  tab: switching tabs doesn't move the page. On phones they take their own line
                  under the title, centered, with "new candidate(s)" on a line of its own, at
                  full width. */}
              <div className="-my-1.5 flex shrink-0 items-center gap-4 max-sm:my-0 max-sm:basis-full max-sm:flex-wrap max-sm:justify-center">
                {current === "topics" ? (
                  <>
                    {ready && (
                      <TryInterview
                        companyId={companyId}
                        interviewId={interview.id}
                        title={interview.title ?? t("fallbackTitle")}
                      />
                    )}
                    {ready && canEdit && (
                      <DeleteInterview
                        interviewId={interview.id}
                        title={interview.title ?? t("fallbackTitle")}
                        leaveTo={interviewsHref}
                      />
                    )}
                  </>
                ) : (
                  current === "candidates" && (
                    <>
                      {interview.candidate_count > 0 && (
                        <InterviewReportActions
                          interviewId={interview.id}
                          title={interview.title ?? ""}
                        />
                      )}
                      {canEdit && (
                        <InviteCandidate
                          interviewId={interview.id}
                          candidatesHref={`${interviewHref}?tab=candidates`}
                          maxInvites={limits?.max_bulk_invites ?? null}
                        />
                      )}
                    </>
                  )
                )}
              </div>
            </div>
          }
        >
          {!ready && canEdit && (
            <Button
              variant="outline"
              className="h-12 px-6 text-base"
              render={
                <Link
                  href={`/generate/${interview.generation_id}?next=${interviewHref}`}
                />
              }
              nativeButton={false}
            >
              {t("continueGeneration")}
            </Button>
          )}
        </PageHeader>
        {ready && (
          <InterviewNav
            href={interviewHref}
            current={current}
            canEdit={canEdit}
          />
        )}
        {/* What it adds up to for each candidate, on the topics tab, once its topics are known. */}
        {current === "topics" &&
          interview.total_questions != null &&
          interview.total_minutes != null && (
            <InterviewEstimate
              questions={interview.total_questions}
              questionSeconds={interview.question_seconds}
              minutes={interview.total_minutes}
            />
          )}
      </div>

      {current === "settings" ? (
        <InterviewSettings
          interviewId={interview.id}
          questionSeconds={interview.question_seconds}
          passMark={interview.pass_mark}
          hired={interview.hired}
        />
      ) : current === "candidates" ? (
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
            path={candidatesPath(status)}
            interviewHref={interviewHref}
            narrowed={Boolean(search || status)}
            initial={candidates ?? []}
            canEdit={canEdit}
          />
        </div>
      ) : (
        <InterviewTopics
          interviewId={id}
          language={interview.language}
          topics={interview.topics}
          canEdit={canEdit}
        />
      )}
    </main>
  )
}
