"use client"

import { useLocale, useTranslations } from "next-intl"

import { ReportActions } from "@/features/company/components/report-actions"
import { REPORT_ID } from "@/config/report"
import { useReportTranslate } from "@/hooks/use-report-translate"
import { reportSummary } from "@/lib/report-summary"
import type { CandidateReportData } from "@/types/company"

/** A candidate's report: download or share it, from their page. */
export function CandidateReportActions({
  interviewId,
  inviteId,
  report,
}: {
  interviewId: string
  inviteId: string
  report: CandidateReportData
}) {
  const t = useTranslations("report")
  const locale = useLocale()
  const translate = useReportTranslate()

  return (
    <ReportActions
      reportId={REPORT_ID}
      fileName={t("fileName", { email: report.email })}
      emailPath={`/companies/interviews/${interviewId}/candidates/${inviteId}/report/email`}
      summary={reportSummary(report, translate, locale)}
    />
  )
}
