import { notFound } from "next/navigation"

import { NewPost } from "@/features/superadmin/components/new-post"
import { NewsAdminList } from "@/features/superadmin/components/news-admin-list"
import { SuperadminHeader } from "@/features/superadmin/components/superadmin-header"
import { PAGE_SIZE } from "@/config/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { AdminNewsPost } from "@/types/news"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** The admin zone's news tab: the news page's posts, written here in English and translated
 * after saving. The API answers superadmins only. */
export default async function NewsAdminPage() {
  const first = await serverFetch<AdminNewsPost[]>(
    `/site/superadmin/news?offset=0&limit=${PAGE_SIZE}`
  )

  if (!first) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <SuperadminHeader current="news" action={<NewPost />}>
        <NewsAdminList initial={first} />
      </SuperadminHeader>
    </main>
  )
}
