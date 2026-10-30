import { cn } from "cn"
import { GiftIcon } from "lucide-react"
import { getLocale, getTranslations } from "next-intl/server"

import { NotesLine } from "@/features/landing/components/notes-line"
import { Receipt } from "@/features/landing/components/receipt"
import { LandingSection, MoreLink } from "@/features/landing/components/section"
import { StartButton } from "@/features/landing/components/start-button"
import { Badge } from "@/components/ui/badge"
import { DEMO_INVITED, FREE_LINES, NOTES } from "@/config/free-to-start-demo"
import { formatPrice } from "@/lib/format"
import type { Catalog } from "@/types/billing"

/** Everything is free, candidates are what's paid for: a receipt for a whole interview where
 * only the candidates who answered cost anything, and beside it the free start and the top-ups,
 * a candidate cheaper the bigger the top-up. Prices from billing's catalog. */
export async function FreeToStartSection({ catalog }: { catalog: Catalog }) {
  const t = await getTranslations("landing.freeToStart")
  const landing = await getTranslations("landing")
  const locale = await getLocale()
  const price = (cents: number) => formatPrice(cents, catalog.currency, locale)
  // The receipt pays for the biggest top-up's candidates at its price, the lowest per candidate.
  const topUp = catalog.products.reduce((best, product) =>
    product.candidate_cents < best.candidate_cents ? product : best
  )

  return (
    <LandingSection id="pricing" title={t("title")} text={t("text")}>
      <div className="flex flex-col items-center gap-10">
        <div className="grid w-full max-w-5xl gap-10 md:grid-cols-2">
          <div className="flex justify-center">
            <Receipt
              free={
                Object.fromEntries(
                  FREE_LINES.map((key) => [
                    key,
                    t(`lines.${key}`, { count: DEMO_INVITED }),
                  ])
                ) as Record<(typeof FREE_LINES)[number], string>
              }
              zero={price(0)}
              paid={t("lines.answered", { count: topUp.candidates })}
              paidAmount={price(topUp.price_cents)}
              totalLabel={t("total")}
              perCandidate={t("each", { price: price(topUp.candidate_cents) })}
            />
          </div>
          <div className="mx-auto flex w-full max-w-md flex-col gap-5 md:mx-0">
            <Badge
              variant="secondary"
              className="h-11 w-full gap-2 rounded-xl px-3 text-sm [&>svg]:size-4!"
            >
              <GiftIcon className="text-primary" />
              {t("free", { count: catalog.free_candidates })}
            </Badge>
            <ul data-testid="price-list" className="divide-y rounded-xl border">
              {catalog.products.map((product) => {
                const used = product.key === topUp.key

                return (
                  <li
                    key={product.key}
                    data-used={used || undefined}
                    className="flex items-baseline justify-between gap-4 px-5 py-3"
                  >
                    <span
                      className={cn(
                        "font-heading text-2xl font-medium tabular-nums",
                        used && "text-primary"
                      )}
                    >
                      {price(product.candidate_cents)}
                      <span
                        className={cn(
                          "ms-1 font-sans text-sm font-normal",
                          used ? "text-primary" : "text-muted-foreground"
                        )}
                      >
                        {t("perCandidate")}
                      </span>
                    </span>
                    <span
                      className={cn(
                        "text-sm whitespace-nowrap text-muted-foreground tabular-nums",
                        used && "font-medium text-primary"
                      )}
                    >
                      {t("pack", {
                        count: product.candidates,
                        price: price(product.price_cents),
                      })}
                    </span>
                  </li>
                )
              })}
            </ul>
            <div className="grid gap-3 sm:grid-cols-2">
              <StartButton
                label={landing("closing.start")}
                className="h-11 px-4 text-base"
              />
              <MoreLink href="/pricing" className="px-4">
                {t("see")}
              </MoreLink>
            </div>
          </div>
        </div>
        <NotesLine notes={NOTES.map((key) => t(`notes.${key}`))} />
      </div>
    </LandingSection>
  )
}
