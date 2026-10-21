import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { QualityList } from "@/components/superadmin/quality-list"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { ReplacedQuestion } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's questions tab, replaced: questions the verifier or an owner replaced, newest
 * first. */
export default async function ReplacedPage() {
  const t = await getTranslations("superadmin")
  const first = await serverFetch<ReplacedQuestion[]>(
    `/library/superadmin/quality/replaced?limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <SuperadminHeader current="questions" sub="replaced" />
      <QualityList
        path="/library/superadmin/quality/replaced"
        initial={first}
        empty={t("noReplaced")}
        byKey
      />
    </main>
  )
}
