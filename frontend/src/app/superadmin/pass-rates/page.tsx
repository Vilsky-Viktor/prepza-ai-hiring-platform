import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { PassRateList } from "@/components/superadmin/pass-rate-list"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { SortMenu } from "@/components/sort-menu"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { PassRate } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

// The orders the API lists pass rates in; the first is its default.
const SORTS = ["pass_rate", "finished"] as const

/** The admin zone's pass rates: company interviews with finished candidates, lowest pass rate
 * or most finished first, for the post-market monitoring routine. */
export default async function PassRatesPage({
  searchParams,
}: {
  searchParams: Promise<{ sort?: string }>
}) {
  const t = await getTranslations("superadmin")
  const candidates = await getTranslations("candidates")
  const { sort: asked } = await searchParams
  const sort = SORTS.find((item) => item === asked) ?? SORTS[0]
  const path = `/companies/superadmin/pass-rates?sort=${sort}`
  const first = await serverFetch<PassRate[]>(`${path}&limit=${PAGE_SIZE}`)

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="pass-rates">
        <div className="space-y-4">
          <div className="flex justify-end">
            {/* A grey pill like the site's selects (components/pill-select.tsx). */}
            <SortMenu
              className="h-12 rounded-xl bg-surface px-5 text-base hover:bg-surface"
              current={sort}
              label={candidates("sortBy", { sort: t(`sortBy.${sort}`) })}
              options={SORTS.map((item) => ({
                value: item,
                label: t(`sortBy.${item}`),
              }))}
            />
          </div>
          <PassRateList path={path} initial={first} />
        </div>
      </SuperadminHeader>
    </main>
  )
}
