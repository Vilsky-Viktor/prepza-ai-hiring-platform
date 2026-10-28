"use client"

import { useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"
import type { CampaignRow } from "@/types/campaigns"

/** Where a campaign stands, as the news tab's "translated" badge: a draft says "translating…"
 * until every language has its texts. */
export function CampaignStatus({ campaign }: { campaign: CampaignRow }) {
  const t = useTranslations("superadmin")
  const translating = campaign.status === "draft" && !campaign.translated

  return (
    <Badge
      variant="outline"
      data-status={campaign.status}
      className="h-7 shrink-0 px-3 text-sm font-light"
    >
      {translating ? t("translating") : t(`campaignStatus.${campaign.status}`)}
    </Badge>
  )
}
