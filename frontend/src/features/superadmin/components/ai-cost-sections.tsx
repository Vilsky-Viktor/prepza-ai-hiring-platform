"use client"

import { useFormatter, useLocale, useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { AmountRows } from "@/features/superadmin/components/amount-rows"
import { NumberCards } from "@/features/superadmin/components/number-cards"
import { useAdminName } from "@/hooks/use-admin-name"
import { hasMessage } from "@/lib/messages"
import { compactNumber, formatPercent, formatUsd } from "@/lib/format"
import type { AiCosts } from "@/types/superadmin"

/** What AI cost in the period, as the API sums it: the totals as cards, today's shared budgets
 * (`budgets`), then lists by who it was for, by action (with what one cost), by model, the
 * companies and users that cost most (each opening its support page), and the spend by day or
 * month. */
export function AiCostSections({
  costs,
  budgets,
}: {
  costs: AiCosts
  budgets: ReactNode
}) {
  const t = useTranslations("superadmin")
  const named = useAdminName()
  const locale = useLocale()
  const format = useFormatter()
  const usd = (value: number) => formatUsd(value, locale)
  const count = (value: number) => compactNumber(value, locale)
  const percent = (share: number) => formatPercent(share * 100, locale)
  const calls = (value: number) => t("aiCalls", { count: value })
  const { totals, month } = costs

  return (
    <>
      <NumberCards
        items={[
          { key: "spend", label: t("aiCards.spend"), value: usd(totals.spend) },
          {
            key: "calls",
            label: t("aiCards.calls"),
            value: count(totals.calls),
          },
          {
            key: "month",
            label: month.budget
              ? t("aiCards.monthOf", { budget: usd(month.budget) })
              : t("aiCards.month"),
            value: usd(month.spend),
          },
          {
            key: "input",
            label: t("aiCards.input"),
            value: count(totals.input_tokens),
          },
          {
            key: "cached",
            label: t("aiCards.cached"),
            value: count(totals.cached_input_tokens),
          },
          {
            key: "output",
            label: t("aiCards.output"),
            value: count(totals.output_tokens),
          },
        ]}
      />
      {budgets}
      <AmountRows
        title={t("aiForTitle")}
        empty={t("aiNothing")}
        rows={costs.categories.map((row) => ({
          key: row.category,
          title: named("aiCategories", row.category),
          details: [percent(row.share), calls(row.calls)],
          amount: usd(row.spend),
        }))}
      />
      <AmountRows
        title={t("aiActionsTitle")}
        empty={t("aiNothing")}
        rows={costs.actions.map((row) => {
          const unitCost = `aiUnitCost.${row.action}` as const
          const cost = usd(row.unit_cost)

          return {
            key: row.action,
            title: named("aiActions", row.action),
            details: [
              hasMessage(t, unitCost) ? t(unitCost, { cost }) : cost,
              calls(row.calls),
              t("aiPaid", { spend: usd(row.paid_spend) }),
              t("aiUnpaid", { spend: usd(row.unpaid_spend) }),
            ],
            amount: usd(row.spend),
          }
        })}
      />
      <AmountRows
        title={t("aiModelsTitle")}
        empty={t("aiNothing")}
        rows={costs.models.map((row) => ({
          key: row.model,
          title: row.model,
          details: [
            calls(row.calls),
            t("aiTokensIn", { count: row.input_tokens }),
            t("aiCachedShare", { share: percent(row.cached_share) }),
            t("aiTokensOut", { count: row.output_tokens }),
          ],
          amount: usd(row.spend),
        }))}
      />
      <AmountRows
        title={t("aiCompaniesTitle")}
        empty={t("aiNothing")}
        rows={costs.companies.map((row) => ({
          key: row.id,
          title: row.name ?? row.id,
          details: [calls(row.calls)],
          amount: usd(row.spend),
          href: `/superadmin/support/companies/${row.id}`,
        }))}
      />
      <AmountRows
        title={t("aiUsersTitle")}
        empty={t("aiNothing")}
        rows={costs.users.map((row) => ({
          key: row.id,
          title: row.name ?? row.id,
          details: [calls(row.calls)],
          amount: usd(row.spend),
          href: `/superadmin/support/users/${row.id}`,
        }))}
      />
      <AmountRows
        title={costs.by_month ? t("aiByMonthTitle") : t("aiByDayTitle")}
        empty={t("aiNothing")}
        rows={costs.days.map((row) => ({
          key: row.day,
          title: (
            <time dateTime={row.day}>
              {format.dateTime(new Date(`${row.day}T12:00:00Z`), {
                ...(costs.by_month ? {} : { day: "numeric" }),
                month: "long",
                year: "numeric",
                timeZone: "UTC",
              })}
            </time>
          ),
          amount: usd(row.spend),
        }))}
      />
    </>
  )
}
