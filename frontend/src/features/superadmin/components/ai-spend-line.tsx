import { getLocale, getTranslations } from "next-intl/server"

import { formatUsd } from "@/lib/format"
import { optionalFetch } from "@/lib/server-api"
import type { AiSpend } from "@/types/superadmin"

/** What AI cost for the company or user (`query`, the API's company_id= or user_id=) over the
 * last days the API counts; null when it doesn't answer. Asked by the page with its own data. */
export function aiSpend(query: string) {
  return optionalFetch<AiSpend>(`/billing/superadmin/ai-spend?${query}`)
}

/** A support page's line about what AI cost (aiSpend); nothing without it. */
export async function AiSpendLine({ spend }: { spend: AiSpend | null }) {
  const [t, locale] = await Promise.all([
    getTranslations("superadmin"),
    getLocale(),
  ])

  if (!spend) {
    return null
  }

  return (
    <p className="text-lg" data-testid="ai-spend">
      {t("supportAiSpend", {
        spend: formatUsd(spend.spend, locale),
        days: spend.days,
        count: spend.calls,
      })}
    </p>
  )
}
