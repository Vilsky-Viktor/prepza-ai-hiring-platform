import { CheckIcon, LinkIcon } from "lucide-react"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"
import { cn } from "cn"
import type { ComponentProps } from "react"

import { BackLink } from "@/components/common/back-link"
import { CopyField } from "@/components/common/copy-field"
import { CornerSign } from "@/components/common/corner-sign"
import { AnswerPatternsCard } from "@/features/company/components/answer-patterns"
import { CandidateActions } from "@/features/company/components/candidate-actions"
import { CandidateReport } from "@/features/company/components/candidate-report"
import { ExtraTime } from "@/features/company/components/extra-time"
import { IntegrityLine } from "@/features/company/components/integrity-line"
import { CandidateReportActions } from "@/features/company/components/candidate-report-actions"
import { ScorecardReview } from "@/components/common/scorecard-review"
import { EditableTitle } from "@/components/common/editable-title"
import { GradeBlock, GradeCard } from "@/components/common/grade-card"
import { NoName } from "@/components/common/no-name"
import { PassStatus } from "@/components/common/pass-status"
import { EntityId } from "@/components/common/entity-id"
import { PageHeader } from "@/components/common/page-header"
import { SignInPage } from "@/components/common/sign-in-page"
import { Badge } from "@/components/ui/badge"
import { InfoCard } from "@/components/common/warning-card"
import { WrappedEmail } from "@/components/common/wrapped-email"
import { SIGN_CARD } from "@/config/cards"
import { MAX_CANDIDATE_NAME_LENGTH } from "@/config/limits"
import { gradeTone } from "@/lib/grade-tone"
import { serverFetch, signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Scorecard } from "@/types/company"
import { formatPercent } from "@/lib/format"
import { candidateReportData } from "@/lib/candidate-report-data"
import { languageOf } from "@/lib/locale"
import { hasMessage } from "@/lib/messages"

export const generateMetadata = () => translatedTitle("candidates", "scorecard")

// A candidate's status by its name, or as the API sent it when there's none.
async function statusName(status: string) {
  const statuses = await getTranslations("candidateStatus")

  return hasMessage(statuses, status) ? statuses(status) : status
}

export default async function ScorecardPage({
  params,
}: {
  params: Promise<{ companyId: string; id: string; inviteId: string }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId, id, inviteId } = await params
  const locale = await getLocale()
  const t = await getTranslations("candidates")
  const card = await serverFetch<Scorecard>(
    `/companies/interviews/${id}/candidates/${inviteId}`
  )

  if (!card) {
    notFound()
  }

  const deleted = card.status === "deleted"

  const reportable = !deleted && card.sessions.length > 0
  const report = candidateReportData(card)

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      {reportable && <CandidateReport report={report} />}
      {/* The actions sit beside the email and status, centered on both. */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          back={
            <BackLink
              href={`/companies/${companyId}/interviews/${id}?tab=candidates`}
              help="candidate"
              // On the email's line, so the info button lines up with the name and status.
              className="wide:inset-y-auto wide:-top-1.5 wide:my-0"
            >
              {t("interview")}
            </BackLink>
          }
          title={
            <div className="space-y-1">
              <h1 className="font-heading text-3xl font-medium tracking-tight">
                {deleted ? t("deleted") : <WrappedEmail email={card.email} />}
              </h1>
              {/* The name and the status on one line, to save one. */}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                {!deleted && (
                  <EditableTitle
                    title={card.name ?? ""}
                    path={`/companies/interviews/${id}/candidates/${inviteId}/name`}
                    maxLength={MAX_CANDIDATE_NAME_LENGTH}
                    editable={card.can_edit}
                    field="name"
                    label={t("name")}
                    editLabel={t("editName")}
                    small
                    emptyLabel={
                      <NoName hint={card.can_edit ? "page" : "view"} />
                    }
                  />
                )}
                <Badge
                  variant={
                    card.status === "undelivered" ? "destructive" : "outline"
                  }
                  className="h-7 px-3 text-sm font-light"
                >
                  {await statusName(card.status)}
                </Badge>
                <EntityId id={inviteId} />
              </div>
            </div>
          }
        />
        {/* On phones the actions take their own line under the name, centered. */}
        {!deleted && (
          <ScorecardActions
            card={card}
            companyId={companyId}
            interviewId={id}
            inviteId={inviteId}
            report={reportable ? report : null}
          />
        )}
      </div>

      {/* The invite link until the interview is finished, in case the email didn't reach the
          candidate or they lost it. */}
      <InviteLink token={card.invite_token} />

      {card.sessions.length > 0 && <ScorecardSummary card={card} />}

      <AnswerPatternsCard
        patterns={card.answer_patterns}
        language={card.language}
      />

      {card.sessions.length === 0 && (
        <p className="py-16 text-center text-muted-foreground">
          {deleted ? t("deletedText") : t("notStarted")}
        </p>
      )}

      {card.sessions.map((session) => {
        const score = session.final_score
        const tone = gradeTone(session.passed) || "text-muted-foreground"

        return (
          <section key={session.id} className="space-y-4">
            {/* On phones the topic, its signals and then its grade, centered. */}
            <div className="flex items-center justify-between gap-4 max-sm:flex-col max-sm:text-center">
              <div className="min-w-0 space-y-1 max-sm:[&_p]:justify-center">
                <h2
                  {...languageOf(card.language)}
                  className="font-heading text-2xl font-medium normal-case"
                >
                  {session.topic_title}
                </h2>
                <IntegrityLine session={session} />
              </div>
              <p className={cn("text-5xl font-light tabular-nums", tone)}>
                {formatPercent(score, locale)}
              </p>
            </div>
            <ScorecardReview items={session.review} language={card.language} />
          </section>
        )
      })}
    </main>
  )
}

/** Beside the email and status: extra time, and for editors the candidate's actions; with a
 * report, its download and sharing. On phones they take their own line under the name,
 * centered. */
function ScorecardActions({
  card,
  companyId,
  interviewId,
  inviteId,
  report,
}: {
  card: Scorecard
  companyId: string
  interviewId: string
  inviteId: string
  report: ComponentProps<typeof CandidateReportActions>["report"] | null
}) {
  return (
    <div className="flex items-center gap-3 max-sm:basis-full max-sm:justify-center">
      <ExtraTime
        interviewId={interviewId}
        inviteId={inviteId}
        current={card.extra_time}
        options={card.extra_time_options}
      />
      {card.can_edit && (
        <CandidateActions
          interviewId={interviewId}
          inviteId={inviteId}
          email={card.email}
          canResend={card.can_resend ?? false}
          revokable={card.revokable ?? false}
          backHref={`/companies/${companyId}/interviews/${interviewId}?tab=candidates`}
        />
      )}
      {report && (
        <CandidateReportActions
          interviewId={interviewId}
          inviteId={inviteId}
          report={report}
        />
      )}
    </div>
  )
}

/** The invite link until the interview is finished, in case the email didn't reach the
 * candidate or they lost it. */
async function InviteLink({ token }: { token?: string | null }) {
  const t = await getTranslations("candidates")

  if (!token) {
    return null
  }

  return (
    <div
      className={cn(SIGN_CARD, "space-y-4 max-sm:-mx-6 max-sm:rounded-none")}
    >
      <CornerSign>
        <LinkIcon className="text-primary" />
      </CornerSign>
      <div className="flex items-center gap-4 text-base">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="font-medium lowercase">{t("inviteLinkTitle")}</p>
          <p className="text-sm text-muted-foreground">{t("inviteLinkHint")}</p>
        </div>
      </div>
      <CopyField path={`/invite/${token}`} />
    </div>
  )
}

/** A started candidate's overall grade, like the practice result's, with whether it passed;
 * then that the score supports a decision people make, in the gray info card, like the
 * practice test page's (on phones it spans the screen, with square corners). Signals are the
 * browser's report: said so wherever they show. */
async function ScorecardSummary({ card }: { card: Scorecard }) {
  const t = await getTranslations("candidates")
  const reportT = await getTranslations("report")
  const locale = await getLocale()
  const signals = card.sessions.some(
    (session) => session.tab_leaves || session.copies || session.fast_answers
  )

  return (
    <>
      <GradeCard>
        <GradeBlock
          value={formatPercent(card.grade, locale)}
          label={t("grade")}
          tone={
            card.passed == null
              ? "text-muted-foreground"
              : gradeTone(card.passed)
          }
        />
        {/* Whether it passed and, under it, small, that they confirmed answering on their own. */}
        <div className="flex flex-col justify-center gap-1 px-8 py-6 text-base max-sm:items-center">
          <PassStatus passed={card.passed} passMark={card.pass_mark} />
          {card.pledged_at && (
            <p
              data-testid="pledged"
              className="flex items-center gap-1.5 text-sm text-muted-foreground"
            >
              <CheckIcon aria-hidden className="size-4 shrink-0" />
              {reportT("pledged")}
            </p>
          )}
        </div>
      </GradeCard>
      <div data-testid="human-review" className="max-sm:-mx-6">
        <InfoCard className="text-sm max-sm:rounded-none">
          {signals ? reportT("humanReviewSignals") : reportT("humanReview")}
        </InfoCard>
      </div>
    </>
  )
}
