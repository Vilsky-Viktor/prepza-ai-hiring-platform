import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { InterviewActions } from "@/components/company/interview-actions"
import { InterviewEstimate } from "@/components/company/interview-estimate"
import { InterviewNav } from "@/components/company/interview-nav"
import { InterviewTitle } from "@/components/company/interview-title"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { INTERVIEW_TAB_HELP } from "@/constants/page-help"
import type { InterviewTab } from "@/lib/interview-page"
import type { InterviewDetail } from "@/types/company"

/** An interview page's header: the way back, its title with its tab's buttons, the way to
 * finish its generation while it isn't ready, its tabs, and on its topics tab what it adds up to
 * for each candidate once its topics are known. */
export async function InterviewHeader({
  interview,
  companyId,
  current,
  maxInvites,
}: {
  interview: InterviewDetail
  companyId: string
  current: InterviewTab
  maxInvites: number | null
}) {
  const t = await getTranslations("interviews")
  const interviewsHref = `/companies/${companyId}/interviews`
  const interviewHref = `${interviewsHref}/${interview.id}`
  const ready = Boolean(interview.set_id)
  // Viewers see everything but change nothing.
  const canEdit = interview.can_edit

  return (
    <div className="space-y-6">
      <PageHeader
        back={
          <BackLink href={interviewsHref} help={INTERVIEW_TAB_HELP[current]}>
            {t("title")}
          </BackLink>
        }
        title={
          <div className="flex items-start justify-between gap-4 max-sm:flex-wrap">
            <InterviewTitle interview={interview} canEdit={canEdit} />
            {/* The test's own actions sit on its tab; inviting, on the candidates tab. The
                  buttons overhang the title's line, so the row is as tall as the title on every
                  tab: switching tabs doesn't move the page. On phones they take their own line
                  under the title, centered, with "new candidate(s)" on a line of its own, at
                  full width. */}
            <div className="-my-1.5 flex shrink-0 items-center gap-4 max-sm:my-0 max-sm:basis-full max-sm:flex-wrap max-sm:justify-center">
              <InterviewActions
                interview={interview}
                companyId={companyId}
                current={current}
                canEdit={canEdit}
                interviewsHref={interviewsHref}
                maxInvites={maxInvites}
              />
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
  )
}
