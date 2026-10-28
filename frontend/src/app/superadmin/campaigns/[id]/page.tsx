import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { CampaignView } from "@/components/superadmin/campaign-view"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Campaign } from "@/types/campaigns"

export const generateMetadata = () => translatedTitle("superadmin", "campaigns")

/** One campaign: its counts, its email as a user in each language gets it, and writing,
 * testing, sending or stopping it. The API answers superadmins only. */
export default async function CampaignPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("superadmin")
  const campaign = await serverFetch<Campaign>(
    `/notifications/superadmin/campaigns/${id}`
  )

  if (!campaign) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <CampaignView
        initial={campaign}
        back={
          <BackLink href="/superadmin/campaigns">{t("campaigns")}</BackLink>
        }
      />
    </main>
  )
}
