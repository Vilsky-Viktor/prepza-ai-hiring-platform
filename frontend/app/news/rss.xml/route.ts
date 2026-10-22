import { getTranslations } from "next-intl/server"

import { DEFAULT_LOCALE } from "@/constants/i18n"
import { NEWS_FEED_SIZE } from "@/constants/news"
import { newsFeed } from "@/lib/news-feed"
import { isLocale } from "@/lib/locale"
import { localizedPath } from "@/lib/locale-path"
import { newsPosts } from "@/lib/news-posts"
import { siteUrl, urlLocale } from "@/lib/site"

/** The news page's RSS feed in the address's language (/de/news/rss.xml), English for the plain
 * address: the newest posts, each in its translation or in English while it has none, read
 * fresh like the page. */
export async function GET() {
  const address = await urlLocale()
  const locale = address && isLocale(address) ? address : DEFAULT_LOCALE
  const t = await getTranslations({ locale, namespace: "news" })
  const posts = await newsPosts(0, NEWS_FEED_SIZE, locale)
  const feed = newsFeed({
    title: t("title"),
    description: t("description"),
    language: locale,
    page: `${siteUrl()}${localizedPath(locale, "/news")}`,
    posts,
  })

  return new Response(feed, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  })
}
