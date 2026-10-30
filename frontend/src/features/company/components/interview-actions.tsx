import { getTranslations } from "next-intl/server"

import { DeleteInterview } from "@/features/company/components/delete-interview"
import { InterviewReportActions } from "@/features/company/components/interview-report-actions"
import { InviteCandidate } from "@/features/company/components/invite-candidate"
import { TryInterview } from "@/features/company/components/try-interview"
import type { InterviewTab } from "@/lib/interview-page"
import type { InterviewDetail } from "@/types/company"

/** The buttons beside an interview's title, by tab: trying and deleting it on its topics,
 * reports and inviting on its candidates; deleting and inviting only for those who can edit. */
export async function InterviewActions({
  interview,
  companyId,
  current,
  canEdit,
  interviewsHref,
  maxInvites,
}: {
  interview: InterviewDetail
  companyId: string
  current: InterviewTab
  canEdit: boolean
  interviewsHref: string
  maxInvites: number | null
}) {
  const t = await getTranslations("interviews")
  const ready = Boolean(interview.set_id)
  const title = interview.title ?? t("fallbackTitle")

  if (current === "topics") {
    return (
      ready && (
        <>
          <TryInterview
            companyId={companyId}
            interviewId={interview.id}
            title={title}
          />
          {canEdit && (
            <DeleteInterview
              interviewId={interview.id}
              title={title}
              leaveTo={interviewsHref}
            />
          )}
        </>
      )
    )
  }

  if (current !== "candidates") {
    return null
  }

  return (
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
          candidatesHref={`${interviewsHref}/${interview.id}?tab=candidates`}
          maxInvites={maxInvites}
        />
      )}
    </>
  )
}
