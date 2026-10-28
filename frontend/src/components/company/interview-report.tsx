"use client"

import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"

import { CompanyLogo } from "@/components/company/company-logo"
import { VerifiedBadge } from "@/components/company/verified-badge"
import { Wordmark } from "@/components/wordmark"
import { WrappedEmail } from "@/components/wrapped-email"
import { Dot, Dotted } from "@/components/dot"
import { INTERVIEW_REPORT_ID } from "@/config/report"
import { gradeTone } from "@/lib/grade-tone"
import type { InterviewReportData } from "@/types/company"
import { formatPercent } from "@/lib/format"

/** All of a test's candidates with their totals, best first, for the PDF: like a candidate's
 * report, a row per candidate instead of a row per topic. It sits off screen, always in the
 * light design, and runs over as many A4 pages as it needs. */
export function InterviewReport({ report }: { report: InterviewReportData }) {
  const t = useTranslations("report")
  const locale = useLocale()
  const candidates = useTranslations("candidates")

  return (
    <div
      id={INTERVIEW_REPORT_ID}
      aria-hidden
      className="light-scope fixed top-0 -left-[10000px] w-[794px] space-y-5 bg-background p-[53px] text-foreground"
    >
      <div className="py-4 text-center">
        <Wordmark className="text-xl" />
      </div>
      {/* The logo on the left of the company and the test, as in a candidate's report. */}
      <div className="flex items-center gap-5">
        {report.logo_url && (
          <CompanyLogo
            url={report.logo_url}
            name={report.company}
            className="h-16 w-auto max-w-40 shrink-0 rounded-xl object-contain"
          />
        )}
        <div className="min-w-0 space-y-1">
          <p className="text-sm text-muted-foreground">
            {report.company}
            {report.verified_domain && (
              <VerifiedBadge
                domain={report.verified_domain}
                className="ms-1 size-4"
              />
            )}
            <Dot />
            {t("candidateCount", { count: report.candidates.length })}
            <Dot />
            {t("passMark", { mark: report.pass_mark })}
          </p>
          <h1 className="font-heading text-2xl font-medium tracking-tight normal-case">
            {report.title}
          </h1>
        </div>
      </div>
      <ul className="divide-y rounded-xl border">
        {report.candidates.map((candidate) => {
          // In words: a PDF has no tooltips to explain icons.
          const signals = [
            candidate.tab_leaves &&
              candidates("pageLeaves", { count: candidate.tab_leaves }),
            candidate.copies &&
              candidates("copies", { count: candidate.copies }),
            candidate.fast_answers &&
              candidates("fastAnswers", { count: candidate.fast_answers }),
          ].filter(Boolean)

          return (
            <li
              key={candidate.id}
              className="flex break-inside-avoid items-center justify-between gap-4 px-4 py-2.5"
            >
              <div className="min-w-0 space-y-0.5">
                <p className="text-base font-medium">
                  <WrappedEmail email={candidate.email} />
                </p>
                {candidate.name && (
                  <p className="text-sm break-all text-muted-foreground">
                    {candidate.name}
                  </p>
                )}
                {signals.length > 0 && (
                  <p className="text-sm text-amber-700">
                    <Dotted items={signals} />
                  </p>
                )}
              </div>
              <div className="flex shrink-0 items-center gap-6">
                <Total label={candidates("progress")}>
                  {formatPercent(candidate.progress, locale)}
                </Total>
                <Total
                  label={candidates("grade")}
                  className={cn(
                    candidate.grade == null && "text-muted-foreground",
                    gradeTone(candidate.passed)
                  )}
                >
                  {formatPercent(candidate.grade, locale)}
                </Total>
              </div>
            </li>
          )
        })}
      </ul>
      <p className="text-xs text-muted-foreground">{t("humanReview")}</p>
    </div>
  )
}

function Total({
  label,
  className,
  children,
}: {
  label: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <div className="w-20 text-center">
      <p className={cn("text-xl font-light tabular-nums", className)}>
        {children}
      </p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
