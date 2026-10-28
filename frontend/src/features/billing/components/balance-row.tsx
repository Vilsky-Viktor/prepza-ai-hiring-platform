"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { BalanceTooltip } from "@/components/common/balance-tooltip"
import { AutoTopUpSetting } from "@/components/common/auto-top-up"
import { TopUpDialog } from "@/components/common/top-up-dialog"
import { useCountUp } from "@/hooks/use-count-up"
import type { Catalog } from "@/types/billing"

/** One balance on the top-up page: whose it is, how much, and a top-up next to it. With
 * `reserved` (the billing page, under the company's own name), the credits set aside for
 * candidates who haven't finished instead of the name. */
export function BalanceRow({
  catalog,
  name,
  available,
  low,
  companyId,
  reserved,
  currency,
}: {
  catalog: Catalog
  name: string
  available: number
  low: boolean
  companyId: string
  reserved?: number
  // The company's currency, beside Top up (the billing page).
  currency?: ReactNode
}) {
  const t = useTranslations("billing")
  // A top-up arriving counts up, as in the header.
  const { shown, rising } = useCountUp(available)

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 px-6 py-5 max-sm:gap-y-5 max-sm:py-7">
      <div className="min-w-0 flex-1 space-y-1 max-sm:basis-full max-sm:text-center">
        {reserved == null && (
          <p className="truncate text-lg font-medium">{name}</p>
        )}
        {!!reserved && (
          <p
            className="text-sm text-muted-foreground"
            data-testid="reserved-credits"
          >
            {t("reserved", { count: reserved })}
          </p>
        )}
        {low && (
          <p className="text-sm text-amber-700 dark:text-amber-400">
            {t("low")}
          </p>
        )}
        <AutoTopUpSetting catalog={catalog} companyId={companyId} />
      </div>
      {/* On phones the balance has its line, and the currency and Top up go under it, together. */}
      <div className="flex items-center gap-6 max-sm:basis-full max-sm:flex-col max-sm:gap-5">
        <p className="text-end">
          <BalanceTooltip
            className={cn(
              "font-heading text-3xl font-medium tabular-nums transition-colors duration-500",
              rising && "text-primary"
            )}
            shown={shown}
            balance={available}
          />{" "}
          <span className="text-sm text-muted-foreground">
            {t("creditsWord", { count: available })}
          </span>
        </p>
        {/* The currency, then Top up, together on phones too. */}
        <div className="flex items-center gap-2 max-sm:gap-3">
          {currency}
          <TopUpDialog title={name} companyId={companyId} />
        </div>
      </div>
    </div>
  )
}
