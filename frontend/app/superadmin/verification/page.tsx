import { notFound } from "next/navigation"

import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { VerificationList } from "@/components/superadmin/verification-list"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { VerificationRequest } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

const PATH = "/companies/superadmin/verifications"

/** The admin zone's verification tab: companies whose domain a work email proved, waiting for
 * review first, then those decided. */
export default async function VerificationPage() {
  const first = await serverFetch<VerificationRequest[]>(
    `${PATH}?limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <SuperadminHeader current="verification">
        <VerificationList path={PATH} initial={first} />
      </SuperadminHeader>
    </main>
  )
}
