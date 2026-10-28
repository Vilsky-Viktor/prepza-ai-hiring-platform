"use client"

import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { flushSync } from "react-dom"

import { InterviewReport } from "@/features/company/components/interview-report"
import { ReportActions } from "@/features/company/components/report-actions"
import { INTERVIEW_REPORT_ID } from "@/config/report"
import { useReportTranslate } from "@/hooks/use-report-translate"
import { apiFetch } from "@/lib/api"
import { candidatesSummary } from "@/lib/report-summary"
import type { InterviewReportData } from "@/types/company"

/** The report of all a test's candidates: download or share it, from its candidates tab. Its
 * data loads on the first click, not with the page. */
export function InterviewReportActions({
  interviewId,
  title,
}: {
  interviewId: string
  title: string
}) {
  const t = useTranslations("report")
  const locale = useLocale()
  const translate = useReportTranslate()
  const [report, setReport] = useState<InterviewReportData | null>(null)

  // Rendered at once, so the hidden report is on the page when the PDF is made from it.
  async function load() {
    if (report) {
      return
    }

    const loaded = await apiFetch<InterviewReportData>(
      `/companies/interviews/${interviewId}/report`
    )
    flushSync(() => setReport(loaded))
  }

  return (
    <>
      {report && <InterviewReport report={report} />}
      <ReportActions
        reportId={INTERVIEW_REPORT_ID}
        fileName={t("candidatesFileName", { title })}
        emailPath={`/companies/interviews/${interviewId}/report/email`}
        summary={report ? candidatesSummary(report, translate, locale) : ""}
        load={load}
        pages
      />
    </>
  )
}
