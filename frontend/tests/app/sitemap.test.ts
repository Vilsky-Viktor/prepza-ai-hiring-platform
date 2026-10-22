import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import sitemap from "@/app/sitemap"

// One guide in English and German, each language's file dated on its own; no templates, and the
// API's news and legal dates unanswered.
vi.mock("@/lib/content", () => ({
  contentPages: vi.fn(async (folder: string) =>
    folder === "guides" ? [{ slug: "dated", updated: "2026-01-01" }] : []
  ),
  contentLanguages: vi.fn(async () => ["en", "de"]),
  contentPage: vi.fn(async (_folder: string, slug: string, locale: string) => ({
    slug,
    language: locale,
    updated: locale === "de" ? "2026-02-02" : "2026-01-01",
  })),
}))
vi.mock("@/lib/server-api", () => ({ publicFetch: vi.fn(async () => []) }))

describe("sitemap", () => {
  beforeEach(() => {
    vi.stubEnv("SITE_URL", "https://prepza.example")
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(null, { status: 503 }))
    )
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it("dates each language of an article by its own file", async () => {
    const entries = await sitemap()
    const date = (url: string) =>
      entries.find((entry) => entry.url === url)?.lastModified

    expect(date("https://prepza.example/guides/dated")).toBe("2026-01-01")
    expect(date("https://prepza.example/de/guides/dated")).toBe("2026-02-02")
  })

  it("names every language's address of a page in absolute hreflang codes", async () => {
    const entries = await sitemap()
    const pricing = entries.find(
      (entry) => entry.url === "https://prepza.example/fil/pricing"
    )

    expect(pricing?.alternates?.languages).toMatchObject({
      tl: "https://prepza.example/fil/pricing",
      "zh-Hans": "https://prepza.example/zh/pricing",
      "x-default": "https://prepza.example/pricing",
    })
  })
})
