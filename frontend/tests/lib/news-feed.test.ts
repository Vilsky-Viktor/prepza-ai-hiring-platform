import { describe, expect, it } from "vitest"

import { escapeXml, newsFeed, rssDate } from "@/lib/news-feed"

const POSTS = [
  {
    id: "b",
    title: "Tom & Jerry <b>hired</b>",
    text: 'Line one.\nSays "hi" & it\'s <script>x</script>',
    published_on: "2026-10-08",
    updated_at: "2026-10-08T09:30:00Z",
  },
  {
    id: "a",
    title: "Older",
    text: "First.",
    published_on: "2026-09-12",
    updated_at: "2026-09-12T08:00:00Z",
  },
]

describe("escapeXml", () => {
  it("escapes every markup character", () => {
    expect(escapeXml(`<a href="x">'&'</a>`)).toBe(
      "&lt;a href=&quot;x&quot;&gt;&apos;&amp;&apos;&lt;/a&gt;"
    )
  })
})

describe("rssDate", () => {
  it("dates a day at midnight UTC, as RFC 822 writes it", () => {
    expect(rssDate("2026-10-08")).toBe("Thu, 08 Oct 2026 00:00:00 GMT")
  })
})

describe("newsFeed", () => {
  const feed = newsFeed({
    title: "testee news",
    description: "What's new",
    language: "de",
    page: "https://testee.dev/de/news",
    posts: POSTS,
  })

  it("names the channel, its page and language", () => {
    expect(feed).toMatch(
      /^<\?xml version="1.0" encoding="UTF-8"\?>\n<rss version="2.0">/
    )
    expect(feed).toContain("<title>testee news</title>")
    expect(feed).toContain("<link>https://testee.dev/de/news</link>")
    expect(feed).toContain("<description>What&apos;s new</description>")
    expect(feed).toContain("<language>de</language>")
  })

  it("keeps the posts in order, as plain text, each linking to its place on the page", () => {
    expect(feed.indexOf('<guid isPermaLink="false">b</guid>')).toBeLessThan(
      feed.indexOf('<guid isPermaLink="false">a</guid>')
    )
    expect(feed).toContain(
      "<title>Tom &amp; Jerry &lt;b&gt;hired&lt;/b&gt;</title>"
    )
    expect(feed).toContain(
      "<description>Line one.\nSays &quot;hi&quot; &amp; it&apos;s &lt;script&gt;x&lt;/script&gt;</description>"
    )
    expect(feed).not.toContain("<script>")
    expect(feed).toContain("<link>https://testee.dev/de/news#b</link>")
    expect(feed).toContain("<pubDate>Thu, 08 Oct 2026 00:00:00 GMT</pubDate>")
  })

  it("is a valid channel without posts", () => {
    expect(
      newsFeed({
        title: "t",
        description: "d",
        language: "en",
        page: "p",
        posts: [],
      })
    ).toContain("<language>en</language>\n  </channel>")
  })
})
