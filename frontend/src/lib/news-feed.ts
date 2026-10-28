import type { NewsPost } from "@/types/news"

/** Text as XML takes it: markup characters escaped, so a post is always plain text. */
export function escapeXml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;")
}

/** A post's day as RSS dates it (RFC 822), at midnight UTC. */
export function rssDate(day: string) {
  return new Date(`${day}T00:00:00Z`).toUTCString()
}

/** The news page's RSS 2.0 feed in one language: `page` is that language's news page, each
 * post links to its place there (#id), in the order given (newest first). */
export function newsFeed({
  title,
  description,
  language,
  page,
  posts,
}: {
  title: string
  description: string
  language: string
  page: string
  posts: NewsPost[]
}) {
  const items = posts.map(
    (post) => `    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${escapeXml(`${page}#${post.id}`)}</link>
      <description>${escapeXml(post.text)}</description>
      <pubDate>${rssDate(post.published_on)}</pubDate>
      <guid isPermaLink="false">${escapeXml(post.id)}</guid>
    </item>`
  )

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>${escapeXml(title)}</title>
    <link>${escapeXml(page)}</link>
    <description>${escapeXml(description)}</description>
    <language>${escapeXml(language)}</language>
${items.map((item) => `${item}\n`).join("")}  </channel>
</rss>
`
}
