import { InfoIcon } from "lucide-react"
import Link from "next/link"
import { getLocale, getTranslations } from "next-intl/server"

import { JsonLd } from "@/components/json-ld"
import { Button } from "@/components/ui/button"
import { InfoCard } from "@/components/warning-card"
import { formatPrice } from "@/lib/format"
import { publicFetch } from "@/lib/server-api"
import { pageMetadata, siteUrl } from "@/lib/site"
import { softwareData } from "@/lib/structured-data"
import type { Catalog } from "@/types/billing"
import { PageKey } from "@/components/page-key"

export async function generateMetadata() {
  const t = await getTranslations("pricing")

  return pageMetadata(t("title"), t("description"), "/pricing", true)
}

// The prices in one bordered list; on phones it spans the screen, with square corners.
const PRICE_LIST = "-mx-6 divide-y border-y sm:mx-0 sm:rounded-xl sm:border"

function PriceRow({ what, price }: { what: string; price: string }) {
  return (
    <li className="flex items-baseline justify-between gap-6 px-5 py-4 max-sm:gap-10 max-sm:px-6">
      <span>{what}</span>
      <span className="max-w-[65%] shrink-0 text-end font-medium tabular-nums">
        {price}
      </span>
    </li>
  )
}

export default async function PricingPage() {
  const t = await getTranslations("pricing")
  const billing = await getTranslations("billing")
  const locale = await getLocale()
  // Billing not answering (starting up, or failing): the page says so instead of its prices,
  // rather than showing nothing or the error page.
  const catalog = await publicFetch<Catalog>("/billing/catalog").catch(
    () => null
  )
  const header = (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4">
        <h1 className="font-heading text-4xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <Button
          className="h-12 px-6 text-base"
          render={<Link href="/top-up" />}
          nativeButton={false}
        >
          {t("topUp")}
        </Button>
      </div>
      <p className="text-base text-muted-foreground">{t("intro")}</p>
    </div>
  )

  if (!catalog) {
    return (
      <main className="mx-auto max-w-5xl space-y-16 px-6 py-12">
        <PageKey page="pricing" />
        {header}
        <InfoCard>{t("unavailable")}</InfoCard>
      </main>
    )
  }

  const [standard, ...volume] = catalog.candidate_prices

  return (
    <main className="mx-auto max-w-5xl space-y-16 px-6 py-12">
      <PageKey page="pricing" />
      <JsonLd data={softwareData(siteUrl(), t("intro"), catalog)} />
      {header}

      <section className="space-y-10">
        <ul className={PRICE_LIST}>
          <PriceRow what={t("test")} price={t("free")} />
          <PriceRow
            what={t("welcome", { count: catalog.free_candidates })}
            price={t("free")}
          />
          <PriceRow
            what={t("candidate")}
            price={t("perCandidate", {
              price: formatPrice(standard.cents, catalog.currency, locale),
            })}
          />
          {/* Volume prices: large top-ups buy more credits per dollar (billing decides). */}
          {volume.map((tier) => (
            <PriceRow
              key={tier.from_dollars}
              what={t("candidateVolume", {
                from: formatPrice(
                  tier.from_dollars * 100,
                  catalog.currency,
                  locale
                ),
              })}
              price={t("perCandidate", {
                price: formatPrice(tier.cents, catalog.currency, locale),
              })}
            />
          ))}
        </ul>
        <div className="space-y-4">
          <div className="mx-auto flex w-fit items-center gap-3 rounded-2xl bg-muted px-5 py-4 text-base text-muted-foreground">
            <InfoIcon aria-hidden className="size-6 shrink-0 text-primary" />
            <p>{t("credits", { credits: catalog.candidate_credits })}</p>
          </div>
          <p className="text-center text-sm text-muted-foreground">
            {billing("taxes")}
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <div className="space-y-1">
          <h2 className="font-heading text-2xl font-medium">
            {t("referrals")}
          </h2>
          <p className="text-base text-muted-foreground">
            {t("referralsNote")}
          </p>
        </div>
        <ul className={PRICE_LIST}>
          <PriceRow
            what={t("companyReferral")}
            price={t("each", { count: catalog.referral_company })}
          />
        </ul>
      </section>
    </main>
  )
}
