import { useLocale, useTranslations } from "next-intl"

import { NumberCards } from "@/features/superadmin/components/number-cards"
import { STATS_CARDS, STATS_SOURCES } from "@/config/stats"
import { compactNumber, compactPrice } from "@/lib/format"
import type { Stats } from "@/types/superadmin"

type Source = (typeof STATS_SOURCES)[number]

/** The numbers as cards (NumberCards), short from a thousand up ("1.5K", "$12.3K"); a dash
 * where the service didn't answer. */
export function StatsCards({ stats }: { stats: Record<Source, Stats | null> }) {
  const t = useTranslations("superadmin")
  const locale = useLocale()

  function value(card: (typeof STATS_CARDS)[number]) {
    const source = stats[card.source]

    // What top-ups paid, in each currency billing sells in that took any ("$12.3K, €4K"), or
    // none in the first.
    if (card.metric === "paid") {
      const paid = Object.entries(source?.paid ?? {})

      if (!paid.length) {
        return "—"
      }

      const taken = paid.filter(([, cents]) => cents > 0)

      return new Intl.ListFormat(locale, { style: "narrow", type: "unit" }).format(
        (taken.length ? taken : paid.slice(0, 1)).map(([currency, cents]) =>
          compactPrice(cents, currency, locale)
        )
      )
    }

    const amount = source?.counts[card.metric]

    if (amount === undefined) {
      return "—"
    }

    return compactNumber(amount, locale)
  }

  return (
    <NumberCards
      items={STATS_CARDS.map((card) => ({
        key: card.metric,
        label: t(`statsCards.${card.metric}`),
        value: value(card),
      }))}
    />
  )
}
