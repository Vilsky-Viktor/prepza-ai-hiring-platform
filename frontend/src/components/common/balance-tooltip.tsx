"use client"

import { useLocale, useTranslations } from "next-intl"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { compactNumber } from "@/lib/format"

/** A balance, short ("250K"), which says the whole amount on hover ("Current balance: 250,000"),
 * and `note` under it (that it runs low). `shown` is the number on screen as it counts up to
 * `balance`. */
export function BalanceTooltip({
  className,
  note,
  shown,
  balance,
}: {
  className?: string
  note?: string
  shown: number
  balance: number
}) {
  const t = useTranslations("billing")
  const locale = useLocale()

  return (
    <Tooltip>
      <TooltipTrigger render={<span className={className} />}>
        {compactNumber(shown, locale)}
      </TooltipTrigger>
      <TooltipContent data-testid="balance-tooltip">
        <p>{t("currentBalance", { amount: balance })}</p>
        {note && <p>{note}</p>}
      </TooltipContent>
    </Tooltip>
  )
}
