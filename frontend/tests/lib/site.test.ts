import { headers } from "next/headers"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { linkLocale, pageMetadata, previewImage } from "@/lib/site"

// lib/site.ts also reads request headers and translations for pages; previewImage uses neither.
vi.mock("next/headers", () => ({ headers: vi.fn() }))
vi.mock("next-intl/server", () => ({
  getLocale: vi.fn(async () => "en"),
  getTranslations: vi.fn(),
}))

describe("previewImage", () => {
  it("draws a page's title in its language", () => {
    const [image] = previewImage("preise", "de")
    const url = new URL(image.url)

    expect(url.pathname).toBe("/preview")
    expect(url.searchParams.get("title")).toBe("preise")
    expect(url.searchParams.get("lang")).toBe("de")
    expect(image).toMatchObject({ width: 1200, height: 630, alt: "preise" })
  })

  it("keeps the site's own picture without a title", () => {
    expect(new URL(previewImage()[0].url).pathname).toBe("/opengraph-image")
  })

  it("keeps the site's own picture in a language it can't draw", () => {
    for (const locale of ["ar", "fa", "he", "hi"]) {
      expect(new URL(previewImage("title", locale)[0].url).pathname).toBe(
        "/opengraph-image"
      )
    }
  })
})

describe("pageMetadata", () => {
  // A plain address: no language prefix.
  beforeEach(() => {
    vi.mocked(headers).mockResolvedValue(new Headers() as never)
  })

  async function pictureTitle(title: string, path: string) {
    const { openGraph } = await pageMetadata(title, "Text.", path)
    const [image] = openGraph?.images as { url: string }[]

    return new URL(image.url).searchParams.get("title")
  }

  it("draws a page's title in lowercase like the site's titles", async () => {
    expect(await pictureTitle("Privacy policy", "/privacy")).toBe(
      "privacy policy"
    )
  })

  it("keeps the API docs' capitals", async () => {
    expect(await pictureTitle("API docs", "/api-docs")).toBe("API docs")
  })
})

describe("pageMetadata's link preview", () => {
  function servedUnder(locale: string | null) {
    vi.mocked(headers).mockResolvedValue(
      new Headers(locale ? { "x-prepza-locale": locale } : {}) as never
    )
  }

  it("names its address, language and the other languages", async () => {
    servedUnder("fil")
    const { openGraph } = await pageMetadata(
      "Presyo",
      "Text.",
      "/pricing",
      true
    )
    const og = openGraph as Record<string, unknown>

    expect(og.url).toBe("/fil/pricing")
    expect(og.locale).toBe("tl")
    expect(og.alternateLocale).toHaveLength(22)
    expect(og.alternateLocale).toContain("zh_Hans")
    expect(og.alternateLocale).not.toContain("tl")
  })

  it("names English for an article not translated into the address's language", async () => {
    servedUnder("de")
    const { openGraph } = await pageMetadata("Guide", "Text.", "/guides/x", [
      "en",
      "fr",
    ])
    const og = openGraph as Record<string, unknown>

    expect(og.url).toBe("/guides/x")
    expect(og.locale).toBe("en")
    expect(og.alternateLocale).toEqual(["fr"])
  })

  it("names one language and no others for a page with one address", async () => {
    servedUnder(null)
    const { openGraph } = await pageMetadata("Terms", "Text.", "/terms")
    const og = openGraph as Record<string, unknown>

    expect(og.locale).toBe("en")
    expect(og.alternateLocale).toBeUndefined()
  })
})

describe("linkLocale", () => {
  function served(found: Record<string, string>) {
    vi.mocked(headers).mockResolvedValue(new Headers(found) as never)
  }

  it("follows the address's language", async () => {
    served({ "x-prepza-locale": "de" })

    expect(await linkLocale("de")).toBe("de")
  })

  it("keeps a plain address's links plain, whatever the interface", async () => {
    served({ "x-prepza-plain": "1" })

    expect(await linkLocale("de")).toBeNull()
  })

  it("follows the interface on a page with one address", async () => {
    served({})

    expect(await linkLocale("de")).toBe("de")
    expect(await linkLocale("en")).toBeNull()
  })
})
