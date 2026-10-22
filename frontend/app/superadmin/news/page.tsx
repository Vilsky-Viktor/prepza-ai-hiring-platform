import { notFound } from "next/navigation"

import { NewPost } from "@/components/superadmin/new-post"
import { NewsAdminList } from "@/components/superadmin/news-admin-list"
import { SuperadminHeader } from "@/components/superadmin/superadmin-header"
import { PAGE_SIZE } from "@/constants/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { AdminNewsPost } from "@/types/news"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's news tab: the news page's posts, written here in English and translated
 * after saving. The API answers superadmins only. */
export default async function NewsAdminPage() {
  const first = await serverFetch<AdminNewsPost[]>(
    `/library/superadmin/news?offset=0&limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <SuperadminHeader current="news" action={<NewPost />}>
        <NewsAdminList initial={first} />
      </SuperadminHeader>
    </main>
  )
}
