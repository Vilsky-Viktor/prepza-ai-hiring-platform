"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

import { useLocalTime } from "@/hooks/use-local-time"
import { DeclineVerification } from "@/components/superadmin/decline-verification"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VirtualList } from "@/components/virtual-list"
import { Dot } from "@/components/dot"
import { usePagedList } from "@/hooks/use-paged-list"
import { apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import { hasMessage } from "@/lib/messages"
import { decisionFailed } from "@/lib/verification"
import type { VerificationRequest } from "@/types/superadmin"
import { LIST_BOX } from "@/config/lists"

function rowKey(row: VerificationRequest) {
  return row.company_id
}

/** Companies sent for review, a page at a time in the API's order (pending first, then those
 * decided): the name and website to check, the work email that proved the domain, and when.
 * A pending one is approved or declined here; one that changed meanwhile reloads instead. */
export function VerificationList({
  path,
  initial,
}: {
  path: string
  initial: VerificationRequest[]
}) {
  const t = useTranslations("superadmin")
  const localTime = useLocalTime()
  const router = useRouter()
  const { items, loadMore } = usePagedList<VerificationRequest>(
    path,
    rowKey,
    initial
  )

  async function approve(row: VerificationRequest) {
    try {
      // The name and domain shown here: a request changed since isn't approved.
      await apiFetch(
        `/companies/superadmin/verifications/${row.company_id}/approve`,
        {
          method: "POST",
          body: JSON.stringify({ name: row.name, domain: row.domain }),
        }
      )
      router.refresh()
    } catch (error) {
      decisionFailed(
        error,
        { changed: t("requestChanged"), failed: t("actionFailed") },
        router.refresh
      )
    }
  }

  if (items.length === 0) {
    return (
      <p className="py-10 text-center text-muted-foreground">
        {t("noVerifications")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={rowKey}
      estimateSize={120}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(row) => {
        const date =
          row.status === "pending" ? row.submitted_at : row.decided_at
        // The list has only requests sent for review: pending or decided.
        const status = `verificationStatus.${row.status}` as const

        return (
          // On phones the status and then the buttons go under the company and its details, each
          // on a centered line of its own.
          <div className="flex items-center gap-6 p-6 max-sm:flex-col max-sm:items-stretch max-sm:gap-4 max-sm:py-8">
            <div className="min-w-0 flex-1 space-y-1">
              <p className="text-lg font-medium">{row.name}</p>
              <p className="text-sm break-words text-muted-foreground">
                <a
                  href={`https://${row.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline underline-offset-4 hover:text-foreground"
                >
                  {row.domain}
                </a>
                {row.email && (
                  <>
                    <Dot />
                    {row.email}
                  </>
                )}
                {date && (
                  <>
                    <Dot />
                    <time dateTime={date} suppressHydrationWarning>
                      {localTime.date(date)}
                    </time>
                  </>
                )}
              </p>
              {row.decline_reason && (
                <p className="text-sm text-muted-foreground">
                  {t.rich("declinedBecause", {
                    reason: row.decline_reason,
                    ...bdi,
                  })}
                </p>
              )}
            </div>
            <div className="flex shrink-0 flex-col items-end gap-2 max-sm:flex-row max-sm:flex-wrap max-sm:items-center max-sm:justify-center max-sm:gap-4">
              <Badge variant="outline" className="h-7 px-3 text-sm font-light">
                {hasMessage(t, status) ? t(status) : row.status}
              </Badge>
              {row.status === "pending" && (
                <span className="flex gap-2 pt-1 max-sm:basis-full max-sm:items-center max-sm:justify-center max-sm:gap-4 max-sm:pt-0">
                  <DeclineVerification
                    companyId={row.company_id}
                    name={row.name}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-sm max-sm:h-10 max-sm:px-5 max-sm:text-base"
                    onClick={() => approve(row)}
                  >
                    {t("approve")}
                  </Button>
                </span>
              )}
            </div>
          </div>
        )
      }}
    />
  )
}
