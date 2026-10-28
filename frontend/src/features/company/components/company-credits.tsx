"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { BalanceTooltip } from "@/components/common/balance-tooltip"
import { RefreshOnFocus } from "@/components/common/refresh-on-focus"
import { TopUpDialog } from "@/components/common/top-up-dialog"
import { useCountUp } from "@/hooks/use-count-up"
import { WARNING_TONE } from "@/config/tones"

/** The company's credits for candidates, with a top-up next to them, in the page header.
 * Without `canEdit` (a viewer) only the balance shows. */
export function CompanyCredits({
  companyId,
  companyName,
  credits,
  low,
  canEdit,
}: {
  companyId: string
  companyName: string
  credits: number
  low: boolean
  canEdit: boolean
}) {
  const t = useTranslations("company")
  // A top-up arriving counts up, as in the header.
  const { shown, rising } = useCountUp(credits)

  const card = (
    <span className="text-base text-muted-foreground max-sm:text-lg">
      <BalanceTooltip
        className={cn(
          "font-medium text-foreground tabular-nums transition-colors duration-500",
          rising && "text-primary",
          low && WARNING_TONE
        )}
        note={low ? t("creditsLow") : undefined}
        shown={shown}
        balance={credits}
      />{" "}
      {t("creditsLeft", { count: credits })}
    </span>
  )

  // A small card in the page header: the balance (amber when it runs low); it opens the top-up.
  // On phones it spans the page, centered, in larger type.
  return (
    <>
      {canEdit ? (
        <TopUpDialog
          title={companyName}
          companyId={companyId}
          card={card}
        />
      ) : (
        <span className="rounded-xl border px-4 py-2 text-end whitespace-nowrap max-sm:text-center">
          {card}
        </span>
      )}
      <RefreshOnFocus />
    </>
  )
}
