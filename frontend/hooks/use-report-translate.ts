import { useTranslations } from "next-intl"

import { bdiText } from "@/lib/bidi"
import type { ReportKey } from "@/lib/report-summary"

/** The texts a report's chat summary is written in: the integrity signals' from the candidates'
 * messages, a candidate's "Name (email)" from the shared ones, the rest from the report's. */
export function useReportTranslate() {
  const t = useTranslations("report")
  const candidates = useTranslations("candidates")
  const common = useTranslations("common")

  return (key: ReportKey, values?: Record<string, string | number>) => {
    if (key === "nameWithEmail") {
      return common.markup(key, { ...values, ...bdiText })
    }

    return key === "pageLeaves" || key === "copies" || key === "fastAnswers"
      ? candidates(key, values)
      : t(key, values)
  }
}
