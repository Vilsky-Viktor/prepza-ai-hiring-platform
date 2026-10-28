import { publicFetch } from "@/lib/server-api"
import type { NewsPost } from "@/types/news"

/** Posts for the news page or its feed, newest first, in the interface language or `locale`.
 * Read fresh, not from the public data cache: a post the admin zone deletes or edits must not
 * stay on the page for minutes. */
export async function newsPosts(
  offset: number,
  limit: number,
  locale?: string
): Promise<NewsPost[]> {
  const posts = await publicFetch<NewsPost[]>(
    `/library/news?offset=${offset}&limit=${limit}`,
    { locale, fresh: true }
  )

  return posts ?? []
}
