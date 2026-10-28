import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { InterviewCandidatesTab } from "@/features/company/components/interview-candidates-tab"
import { InterviewHeader } from "@/features/company/components/interview-header"
import { InterviewSettings } from "@/features/company/components/interview-settings"
import { ShareLink } from "@/features/company/components/share-link"
import { InterviewTopics } from "@/features/company/components/interview-topics"
import { WhatsNext } from "@/features/company/components/whats-next"
import { SignInPage } from "@/components/common/sign-in-page"
import { READY_PARAM } from "@/config/interviews"
import {
  type InterviewQuery,
  interviewTab,
  loadInterviewPage,
} from "@/lib/interview-page"
import { signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"

export const generateMetadata = () => translatedTitle("interviews", "interview")

export default async function InterviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string; id: string }>
  searchParams: Promise<InterviewQuery>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId, id } = await params
  const query = await searchParams
  const t = await getTranslations("interviews")
  const { interview, filters, candidates, limits, sort, search, status } =
    await loadInterviewPage(id, query)

  if (!interview) {
    notFound()
  }

  const interviewsHref = `/companies/${companyId}/interviews`
  const interviewHref = `${interviewsHref}/${id}`
  const ready = Boolean(interview.set_id)
  // Viewers see everything but change nothing.
  const canEdit = interview.can_edit
  const current = interviewTab(query.tab, ready, canEdit)

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      {/* Just generated: what to do next, for those who can do it. */}
      {ready && canEdit && query[READY_PARAM] && (
        <WhatsNext
          title={interview.title ?? t("fallbackTitle")}
          interviewHref={interviewHref}
        />
      )}
      <InterviewHeader
        interview={interview}
        companyId={companyId}
        current={current}
        maxInvites={limits?.max_bulk_invites ?? null}
      >
        {current === "settings" ? (
          // The shareable link sits with the interview's settings, above them.
          <div className="space-y-6">
            <ShareLink
              interviewId={interview.id}
              linkToken={interview.link_token}
              canEdit={canEdit}
            />
            <InterviewSettings
              interviewId={interview.id}
              questionSeconds={interview.question_seconds}
              passMark={interview.pass_mark}
              hired={interview.hired}
              keepPrivate={interview.keep_private}
            />
          </div>
        ) : current === "candidates" ? (
          <InterviewCandidatesTab
            interview={interview}
            interviewHref={interviewHref}
            canEdit={canEdit}
            sort={sort}
            search={search}
            status={status}
            filters={filters}
            candidates={candidates}
          />
        ) : (
          <InterviewTopics
            interviewId={id}
            language={interview.language}
            topics={interview.topics}
            canEdit={canEdit}
          />
        )}
      </InterviewHeader>
    </main>
  )
}
