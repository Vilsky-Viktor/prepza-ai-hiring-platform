"use client"

import { useLocale, useTranslations } from "next-intl"

import { AmountRows } from "@/features/superadmin/components/amount-rows"
import { useAdminName } from "@/hooks/use-admin-name"
import {
  compactNumber,
  formatPercent,
  formatSeconds,
  formatUsd,
} from "@/lib/format"
import type { AiCosts, Budget } from "@/types/superadmin"

/** A limit's amount as its unit reads: dollars, a percentage, seconds, or a short count
 * ("200M"). */
export function useLimitAmount() {
  const locale = useLocale()

  return (value: number, unit: string | null | undefined) => {
    if (unit === "usd") {
      return formatUsd(value, locale)
    }

    if (unit === "percent") {
      return formatPercent(value, locale)
    }

    if (unit === "seconds") {
      return formatSeconds(value, locale)
    }

    return compactNumber(value, locale)
  }
}

/** How much of each shared daily budget is used today: the unpaid users' AI spend against its
 * cap first, then each owning service's budgets, "used of limit" with the share used. */
export function AiBudgets({
  unpaid,
  budgets,
}: {
  unpaid: AiCosts["unpaid_today"]
  budgets: Budget[]
}) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const amount = useLimitAmount()
  const named = useAdminName()

  return (
    <AmountRows
      title={t("aiBudgetsTitle")}
      empty={t("aiNothing")}
      rows={[
        {
          key: "AI_SPEND_UNPAID_DAY",
          title: t("limitNames.AI_SPEND_UNPAID_DAY"),
          details: [formatPercent(unpaid.share * 100, locale)],
          amount: t("aiOf", {
            used: formatUsd(unpaid.spend, locale),
            limit: formatUsd(unpaid.cap, locale),
          }),
        },
        ...budgets.map((budget) => ({
          key: budget.name,
          title: named("limitNames", budget.name),
          details: [formatPercent(budget.share * 100, locale)],
          amount: t("aiOf", {
            used: amount(budget.used, budget.unit),
            limit: amount(budget.limit, budget.unit),
          }),
        })),
      ]}
    />
  )
}
