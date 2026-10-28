import { getLocale, getTranslations } from "next-intl/server"
import { cn } from "cn"

import { CompanyLogo } from "@/components/common/company-logo"
import { IntegrityLine } from "@/features/company/components/integrity-line"
import { PassStatus } from "@/components/common/pass-status"
import { VerifiedBadge } from "@/components/common/verified-badge"
import { Wordmark } from "@/components/common/wordmark"
import { Dot } from "@/components/common/dot"
import { REPORT_ID } from "@/config/report"
import { gradeTone } from "@/lib/grade-tone"
import type { CandidateReportData } from "@/types/company"
import { formatPercent } from "@/lib/format"
import { languageOf } from "@/lib/locale"

/** The candidate's report the PDF is made from: one compact A4-wide page with the logo, the
 * overall result and each topic's score and signals, never the questions. It sits off screen,
 * always in the light design. */
export async function CandidateReport({
  report,
}: {
  report: CandidateReportData
}) {
  const { company, logoUrl, title, email, grade, passed, passMark, sections } =
    report
  const t = await getTranslations("report")
  const locale = await getLocale()

  return (
    <div
      id={REPORT_ID}
      aria-hidden
      className="light-scope fixed top-0 -left-[10000px] w-[794px] space-y-5 bg-background p-[53px] text-foreground"
    >
      <div className="py-4 text-center">
        <Wordmark className="text-xl" />
      </div>
      {/* The logo on the left of the test and the candidate's email, with their name. */}
      <div className="flex items-center gap-5">
        {logoUrl && (
          <CompanyLogo
            url={logoUrl}
            name={company}
            className="h-16 w-auto max-w-40 shrink-0 rounded-xl object-contain"
          />
        )}
        <div className="min-w-0 space-y-1">
          <p className="text-sm text-muted-foreground">
            {company}
            {report.verifiedDomain && (
              <VerifiedBadge
                domain={report.verifiedDomain}
                className="ms-1 size-4"
              />
            )}
            {title && (
              <>
                <Dot />
                {title}
              </>
            )}
          </p>
          <h1 className="font-heading text-2xl font-medium tracking-tight break-all">
            {email}
          </h1>
          {report.name && (
            <p className="text-sm break-all text-muted-foreground">
              {report.name}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-baseline gap-3">
        <p
          className={cn(
            "text-4xl font-light tabular-nums",
            gradeTone(passed),
            grade == null && "text-muted-foreground"
          )}
        >
          {formatPercent(grade, locale)}
        </p>
        <p className="text-sm">
          <PassStatus passed={passed} passMark={passMark} />
        </p>
      </div>
      <ul className="divide-y rounded-xl border">
        {sections.map((section) => (
          <li
            key={section.id}
            className="flex break-inside-avoid items-center justify-between gap-4 px-4 py-2.5"
          >
            <div className="min-w-0 space-y-0.5">
              <h2
                {...languageOf(report.language)}
                className="text-base font-medium"
              >
                {section.topic_title}
              </h2>
              <IntegrityLine session={section} />
            </div>
            <p
              className={cn(
                "text-xl font-light tabular-nums",
                gradeTone(section.passed),
                section.final_score == null && "text-muted-foreground"
              )}
            >
              {formatPercent(section.final_score, locale)}
            </p>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        {sections.some(
          (section) =>
            section.tab_leaves || section.copies || section.fast_answers
        )
          ? t("humanReviewSignals")
          : t("humanReview")}
      </p>
    </div>
  )
}
