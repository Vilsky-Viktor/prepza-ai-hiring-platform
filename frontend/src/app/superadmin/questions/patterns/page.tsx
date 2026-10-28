import { notFound } from "next/navigation"

import { PatternList } from "@/components/superadmin/pattern-list"
import { PatternStatusFilter } from "@/components/superadmin/pattern-status-filter"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { PAGE_SIZE } from "@/config/lists"
import { PATTERN_STATUSES } from "@/config/patterns"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { QualityPattern } from "@/types/generation"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's questions tab, patterns: recurring mistakes the weekly job found in flagged
 * and replaced questions, written as general rules, to approve or dismiss. Proposed ones first;
 * the status pill lists the others. */
export default async function PatternsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>
}) {
  const { status: asked } = await searchParams
  const status =
    PATTERN_STATUSES.find((item) => item === asked) ?? PATTERN_STATUSES[0]
  const path = `/generate/superadmin/patterns?status=${status}`
  const first = await serverFetch<QualityPattern[]>(
    `${path}&limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="questions" sub="patterns">
        <div className="space-y-4">
          <div className="flex justify-end">
            <PatternStatusFilter current={status} />
          </div>
          {/* Remounted for each status: what was reviewed on the last one isn't hidden here. */}
          <PatternList key={status} path={path} initial={first} />
        </div>
      </SuperadminHeader>
    </main>
  )
}
