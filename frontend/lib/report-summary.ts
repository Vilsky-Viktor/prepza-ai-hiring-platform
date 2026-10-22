import type { CandidateReportData, InterviewReportData } from "@/types/company"
import { formatList, formatPercent } from "@/lib/format"
import type { MessageKey } from "@/types/messages"

// The keys a summary is written with: the report's, the candidates' signal counts and the
// shared "Name (email)" (useReportTranslate finds each in its group).
export type ReportKey =
  | MessageKey<"report">
  | "pageLeaves"
  | "copies"
  | "fastAnswers"
  | "nameWithEmail"

type Translate = (
  key: ReportKey,
  values?: Record<string, string | number>
) => string

/** A candidate as a message names them: "Name (email)", or the email while the name is
 * unknown. */
export function candidateLabel(
  candidate: { email: string; name?: string | null },
  t: Translate
) {
  return candidate.name
    ? t("nameWithEmail", { name: candidate.name, email: candidate.email })
    : candidate.email
}

/** The candidate's result as a short chat message, for WhatsApp and Telegram, which can't carry
 * the PDF: the test, the overall result, then each topic's score and any signals. */
export function reportSummary(
  report: CandidateReportData,
  t: Translate,
  locale: string
) {
  const result =
    report.passed == null
      ? t("notFinished")
      : t(report.passed ? "passed" : "notPassed", {
          mark: formatPercent(report.passMark, locale),
        })
  const topics = report.sections.map((section) => {
    const signals = [
      section.tab_leaves && t("pageLeaves", { count: section.tab_leaves }),
      section.copies && t("copies", { count: section.copies }),
      section.fast_answers && t("fastAnswers", { count: section.fast_answers }),
    ].filter(Boolean) as string[]
    const score = formatPercent(section.final_score, locale)

    return `• ${section.topic_title}: ${formatList([score, ...signals], locale)}`
  })

  return [
    [report.company, report.title].filter(Boolean).join(" · "),
    `${candidateLabel(report, t)}: ${formatList([formatPercent(report.grade, locale), result], locale)}`,
    "",
    ...topics,
    "",
    t("via"),
  ].join("\n")
}

/** All of a test's candidates as a short chat message: the test and its passing grade, then
 * each candidate's grade, progress and any signals, best first. */
export function candidatesSummary(
  report: InterviewReportData,
  t: Translate,
  locale: string
) {
  const rows = report.candidates.map((candidate) => {
    const signals = [
      candidate.tab_leaves && t("pageLeaves", { count: candidate.tab_leaves }),
      candidate.copies && t("copies", { count: candidate.copies }),
      candidate.fast_answers &&
        t("fastAnswers", { count: candidate.fast_answers }),
    ].filter(Boolean) as string[]
    const grade = formatPercent(candidate.grade, locale)
    const progress = t("progressOf", {
      progress: formatPercent(candidate.progress, locale),
    })

    return `• ${candidateLabel(candidate, t)}: ${formatList([grade, progress, ...signals], locale)}`
  })

  return [
    [report.company, report.title].filter(Boolean).join(" · "),
    t("passMark", { mark: formatPercent(report.pass_mark, locale) }),
    "",
    ...rows,
    "",
    t("via"),
  ].join("\n")
}
