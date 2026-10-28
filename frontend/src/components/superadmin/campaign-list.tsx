"use client"

import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"

import { Dotted } from "@/components/dot"
import { CampaignStatus } from "@/components/superadmin/campaign-status"
import { VirtualList } from "@/components/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { formatDate } from "@/lib/format"
import { byId } from "@/lib/paged-list"
import type { CampaignRow } from "@/types/campaigns"

/** The campaigns, newest first, like the news tab's posts: each its subject, kind and day, and
 * once sent its counts; a badge says where it stands. A row opens the campaign. */
export function CampaignList({ initial }: { initial: CampaignRow[] }) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const { items, loadMore } = usePagedList(
    "/notifications/superadmin/campaigns",
    byId,
    initial
  )

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        {t("noCampaigns")}
      </p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={89}
      onEndReached={loadMore}
      className={LIST_BOX}
      renderItem={(campaign) => (
        // On phones the status takes the line under the subject.
        <Link
          href={`/superadmin/campaigns/${campaign.id}`}
          className={`flex items-center gap-6 p-6 ${ROW_HOVER} max-sm:flex-wrap max-sm:gap-y-3`}
        >
          <div className="min-w-0 flex-1 space-y-1 max-sm:basis-full">
            <span className="block text-lg font-medium break-words normal-case sm:truncate">
              {campaign.subject}
            </span>
            <span className="block text-sm text-muted-foreground">
              <Dotted
                items={[
                  t(`campaignKinds.${campaign.kind}`),
                  <time
                    key="sent"
                    dateTime={campaign.sent_at ?? campaign.created_at}
                  >
                    {formatDate(
                      campaign.sent_at ?? campaign.created_at,
                      locale
                    )}
                  </time>,
                  ...(campaign.counts
                    ? (
                        [
                          "sent",
                          "skipped",
                          "failed",
                          "unsubscribed",
                          "complained",
                        ] as const
                      ).map((key) =>
                        t(`campaignRowCounts.${key}`, {
                          count: campaign.counts![key],
                        })
                      )
                    : []),
                ]}
              />
            </span>
          </div>
          <CampaignStatus campaign={campaign} />
        </Link>
      )}
    />
  )
}
