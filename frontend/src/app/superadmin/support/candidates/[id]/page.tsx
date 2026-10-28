import Link from "next/link"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { EntityId } from "@/components/common/entity-id"
import { LocalDate } from "@/components/common/local-date"
import { PageHeader } from "@/components/common/page-header"
import { AddressSuppression } from "@/features/superadmin/components/address-suppression"
import { CandidateEmailStops } from "@/features/superadmin/components/candidate-email-stops"
import { SupportFacts } from "@/features/superadmin/components/support-facts"
import { Badge } from "@/components/ui/badge"
import { WrappedEmail } from "@/components/common/wrapped-email"
import { DottedText } from "@/components/common/dot"
import { formatPercent } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { SupportCandidate } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

const LINK = "underline underline-offset-4 normal-case"

/** A candidate in the admin zone's support tab: what happened to their invite (sent, started,
 * finished, graded, charged), never their questions or answers; and the company emails their
 * address stopped, stopped or let through again here. The API answers superadmins only and
 * logs each look. */
export default async function SupportCandidatePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("superadmin")
  const statuses = await getTranslations("candidateStatus")
  const locale = await getLocale()
  const candidate = await serverFetch<SupportCandidate>(
    `/companies/superadmin/support/candidates/${id}`
  )

  if (!candidate) {
    notFound()
  }

  const date = (iso: string | null | undefined) =>
    iso ? <LocalDate iso={iso} withTime /> : t("supportNotYet")
  const { signals } = candidate

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageHeader
        back={<BackLink href="/superadmin/support">{t("support")}</BackLink>}
        title={
          <div className="space-y-1">
            <h1 className="font-heading text-3xl font-medium tracking-tight">
              <WrappedEmail email={candidate.email} />
            </h1>
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              {candidate.name && (
                <span className="normal-case">{candidate.name}</span>
              )}
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {hasMessage(statuses, candidate.status)
                  ? statuses(candidate.status)
                  : candidate.status}
              </Badge>
              <EntityId id={candidate.invite_id} />
            </p>
          </div>
        }
      />

      <SupportFacts
        facts={[
          [
            t("supportFacts.company"),
            <Link
              key="company"
              href={`/superadmin/support/companies/${candidate.company_id}`}
              className={LINK}
            >
              {candidate.company_name}
            </Link>,
          ],
          [
            t("supportFacts.interview"),
            <Link
              key="interview"
              href={`/superadmin/support/interviews/${candidate.interview_id}`}
              className={LINK}
            >
              {candidate.interview_title ?? t("supportUntitled")}
            </Link>,
          ],
          [t("supportFacts.invited"), date(candidate.invited_at)],
          [t("supportFacts.lastSent"), date(candidate.last_sent_at)],
          [t("supportFacts.started"), date(candidate.started_at)],
          [t("supportFacts.finished"), date(candidate.finished_at)],
          [
            t("supportFacts.grade"),
            candidate.grade == null
              ? null
              : t(candidate.passed ? "supportPassed" : "supportNotPassed", {
                  grade: formatPercent(candidate.grade, locale),
                }),
          ],
          [
            t("supportFacts.extraTime"),
            candidate.extra_time
              ? formatPercent(candidate.extra_time, locale, true)
              : t("supportNoExtraTime"),
          ],
          [
            t("supportFacts.signals"),
            <DottedText
              key="signals"
              text={t("supportSignals", {
                leaves: signals.tab_leaves,
                copies: signals.copies,
                fast: signals.fast_answers,
              })}
            />,
          ],
          [
            t("supportFacts.credits"),
            candidate.credits ? t(`supportCredits.${candidate.credits}`) : null,
          ],
        ]}
      />

      <AddressSuppression email={candidate.email} />
      <CandidateEmailStops email={candidate.email} />
    </main>
  )
}
