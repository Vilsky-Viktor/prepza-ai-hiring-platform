import { notFound } from "next/navigation"

import { CampaignList } from "@/components/superadmin/campaign-list"
import { NewCampaign } from "@/components/superadmin/new-campaign"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { PAGE_SIZE } from "@/constants/lists"
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
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <SuperadminHeader current="campaigns" action={<NewCampaign />}>
        <CampaignList initial={first} />
      </SuperadminHeader>
    </main>
  )
}
