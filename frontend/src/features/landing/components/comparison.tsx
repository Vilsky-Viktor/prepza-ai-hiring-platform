import { cn } from "cn"
import { CalendarSyncIcon, PhoneIcon, type LucideIcon } from "lucide-react"
import { getLocale, getTranslations } from "next-intl/server"

import { LandingSection, MoreLink } from "@/features/landing/components/section"
import { COMPARED } from "@/config/comparison"
import { BAND } from "@/config/landing-backgrounds"
import { candidatePriceRange } from "@/lib/format"
import type { Catalog } from "@/types/billing"

const ICONS: Record<
  Exclude<(typeof COMPARED)[number], "prepza">,
  LucideIcon
> = {
  phone: PhoneIcon,
  subscription: CalendarSyncIcon,
}

/** prepza beside the usual ways to screen candidates: a card each with what it checks, what it
 * takes of your time and what you pay, prepza's last and ringed; then a link to the comparisons with other
 * tools. prepza's price range per candidate comes from billing's catalog. */
export async function ComparisonSection({ catalog }: { catalog: Catalog }) {
  const t = await getTranslations("landing.comparison")
  const locale = await getLocale()
  const price = candidatePriceRange(catalog, locale)

  return (
    <LandingSection
      id="compare"
      title={t("title")}
      text={t("text")}
      background={BAND}
    >
      <div className="flex flex-col items-center gap-10">
        {/* On the section's grey band, the cards in the page's colour. */}
        <ul className="grid w-full gap-3 md:grid-cols-3">
          {COMPARED.map((key) => {
            const ours = key === "prepza"
            const Icon = ours ? null : ICONS[key]

            return (
              <li
                key={key}
                className={cn(
                  "flex flex-col gap-6 rounded-xl bg-background p-6 sm:p-8 lg:p-10",
                  ours && "border-primary-gradient relative"
                )}
              >
                <div className="flex min-h-8 items-center gap-3">
                  {Icon && (
                    <Icon className="size-6 shrink-0 text-muted-foreground" />
                  )}
                  <span className="font-heading text-xl font-medium lowercase">
                    {t(`${key}.name`)}
                    {ours && <span className="text-primary">.</span>}
                  </span>
                </div>
                {(["checks", "time", "cost"] as const).map((fact) => (
                  <div key={fact} className="space-y-1">
                    <p className="text-sm text-muted-foreground">{t(fact)}</p>
                    <p
                      className={cn(
                        "text-lg leading-snug font-medium",
                        ours && "text-primary"
                      )}
                    >
                      {t(`${key}.${fact}`, { price })}
                    </p>
                  </div>
                ))}
              </li>
            )
          })}
        </ul>
        <MoreLink href="/compare">{t("more")}</MoreLink>
      </div>
    </LandingSection>
  )
}
