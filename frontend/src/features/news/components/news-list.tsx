"use client"

import { useLocale, useTranslations } from "next-intl"

import { VirtualList } from "@/components/common/virtual-list"
import { usePagedList } from "@/hooks/use-paged-list"
import { formatDay } from "@/lib/format"
import { postHeading } from "@/lib/news"
import { byId } from "@/lib/paged-list"
import type { NewsPost } from "@/types/news"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"

/** The news page's posts, newest first, one after another. `initial` is the server's first
 * page; the next loads near the end. */
export function NewsList({ initial }: { initial: NewsPost[] }) {
  const t = useTranslations("news")
  const { items, loadMore } = usePagedList("/library/news", byId, initial)

  if (items.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">{t("empty")}</p>
    )
  }

  return (
    <VirtualList
      items={items}
      getKey={byId}
      estimateSize={160}
      onEndReached={loadMore}
      className={`${LIST_BOX} overflow-hidden`}
      renderItem={(post) => <Post post={post} />}
    />
  )
}

/** One post: its title with the site's blue dot, as an article's section heading, its day just
 * under it, and its text as plain text with its line breaks. Its id is the feed's link to it. */
function Post({ post }: { post: NewsPost }) {
  const locale = useLocale()
  const heading = postHeading(post.title)

  return (
    <article id={post.id} className={`space-y-3 p-6 ${ROW_HOVER} max-sm:py-9`}>
      <div className="space-y-1">
        <h2 className="no-dot font-heading text-2xl font-medium break-words normal-case">
          {heading.text}
          {heading.dot && <span className="text-primary">.</span>}
        </h2>
        <p className="text-sm text-muted-foreground italic">
          <time dateTime={post.published_on}>
            {formatDay(post.published_on, locale)}
          </time>
        </p>
      </div>
      <p className="text-base leading-relaxed break-words whitespace-pre-line">
        {post.text}
      </p>
    </article>
  )
}
