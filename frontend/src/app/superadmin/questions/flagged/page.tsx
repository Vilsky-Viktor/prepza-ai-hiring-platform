import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { QualityList } from "@/components/superadmin/quality-list"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { FlaggedQuestion } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's questions tab, flagged: questions waiting for the verifier, newest first.
 */
export default async function FlaggedPage() {
  const t = await getTranslations("superadmin")
  const first = await serverFetch<FlaggedQuestion[]>(
    `/library/superadmin/quality/flagged?limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="questions" sub="flagged">
        <QualityList
          path="/library/superadmin/quality/flagged"
          initial={first}
          empty={t("noFlagged")}
        />
      </SuperadminHeader>
    </main>
  )
}
