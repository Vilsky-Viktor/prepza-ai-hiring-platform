import { notFound } from "next/navigation"

import { CampaignList } from "@/features/superadmin/components/campaign-list"
import { NewCampaign } from "@/features/superadmin/components/new-campaign"
import { SuperadminHeader } from "@/features/superadmin/components/superadmin-header"
import { PAGE_SIZE } from "@/config/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { CampaignRow } from "@/types/campaigns"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's campaigns tab, like the news tab: product updates and offers to the users
 * who chose them, newest first. The API answers superadmins only. */
export default async function CampaignsPage() {
  const first = await serverFetch<CampaignRow[]>(
    `/notifications/superadmin/campaigns?offset=0&limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="campaigns" action={<NewCampaign />}>
        <CampaignList initial={first} />
      </SuperadminHeader>
    </main>
  )
}
