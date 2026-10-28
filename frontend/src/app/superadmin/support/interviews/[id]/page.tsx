import Link from "next/link"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { EntityId } from "@/components/entity-id"
import { LocalDate } from "@/components/local-date"
import { PageHeader } from "@/components/page-header"
import { SupportFacts } from "@/components/superadmin/support-facts"
import { SupportInterviewCandidates } from "@/components/superadmin/support-lists"
import { Badge } from "@/components/ui/badge"
import { PAGE_SIZE } from "@/constants/lists"
import { formatPercent } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { SupportCandidateRow, SupportInterview } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** An interview in the admin zone's support tab: whose it is, whether its generation failed,
 * its topics and settings, and its candidates, each opening their page. The API answers
 * superadmins only and logs each look. */
export default async function SupportInterviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("superadmin")
  const statuses = await getTranslations("interviewStatus")
  const locale = await getLocale()
  const api = `/companies/superadmin/support/interviews/${id}`
  const [interview, candidates] = await Promise.all([
    serverFetch<SupportInterview>(api),
    serverFetch<SupportCandidateRow[]>(`${api}/candidates?limit=${PAGE_SIZE}`),
  ])

  if (!interview) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageHeader
        back={<BackLink href="/superadmin/support">{t("support")}</BackLink>}
        title={
          <div className="space-y-1">
            <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
              {interview.title ?? t("supportUntitled")}
            </h1>
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              {interview.generation_failed ? (
                <Badge
                  variant="destructive"
                  className="h-7 px-3 text-sm font-light"
                >
                  {t("supportGenerationFailed")}
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="h-7 px-3 text-sm font-light"
                >
                  {hasMessage(statuses, interview.status)
                    ? statuses(interview.status)
                    : interview.status}
                </Badge>
              )}
              <EntityId id={interview.id} />
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
              href={`/superadmin/support/companies/${interview.company_id}`}
              className="normal-case underline underline-offset-4"
            >
              {interview.company_name}
            </Link>,
          ],
          [
            t("supportCreated"),
            <LocalDate key="created" iso={interview.created_at} withTime />,
          ],
          [
            t("supportFacts.questionSeconds"),
            t("supportSeconds", { count: interview.question_seconds }),
          ],
          [
            t("supportFacts.passMark"),
            formatPercent(interview.pass_mark, locale),
          ],
        ]}
      />

      {/* The topics as tags, like a practice page's; a long name wraps inside its tag. */}
      {interview.topics.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-medium">{t("supportFacts.topics")}</h2>
          <div className="flex flex-wrap gap-2">
            {interview.topics.map((topic) => (
              <Badge
                key={topic}
                variant="outline"
                className="h-auto min-h-7 px-3 py-1 text-sm font-light whitespace-normal normal-case"
              >
                {topic}
              </Badge>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-4">
        <h2 className="text-lg font-medium">
          {t("supportCandidates", { count: interview.candidate_count })}
        </h2>
        <SupportInterviewCandidates api={api} initial={candidates ?? []} />
      </section>
    </main>
  )
}
