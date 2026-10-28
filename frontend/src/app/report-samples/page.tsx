import { notFound } from "next/navigation"

import { CandidateReport } from "@/components/company/candidate-report"
import { InterviewReport } from "@/components/company/interview-report"
import { ReportActions } from "@/components/company/report-actions"
import { INTERVIEW_REPORT_ID, REPORT_ID } from "@/config/report"
import {
  CANDIDATE_SAMPLE,
  INTERVIEW_SAMPLE,
} from "@/config/report-samples-fixture"

/** The landing's sample reports, made from made-up data by the same reports and download
 * buttons as a company's pages: scripts/report-samples.sh clicks both. Development only. */
export default function ReportSamplesPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-x-4 px-6 py-12">
      <CandidateReport report={CANDIDATE_SAMPLE} />
      <InterviewReport report={INTERVIEW_SAMPLE} />
      <ReportActions
        reportId={INTERVIEW_REPORT_ID}
        fileName="prepza-sample-candidates"
        emailPath=""
        summary=""
        pages
      />
      <ReportActions
        reportId={REPORT_ID}
        fileName="prepza-sample-candidate-report"
        emailPath=""
        summary=""
      />
    </main>
  )
}
