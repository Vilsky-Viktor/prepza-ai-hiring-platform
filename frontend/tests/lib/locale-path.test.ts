import { describe, expect, it } from "vitest"

import {
  isLocalizedPath,
  hasLanguageVersions,
  hreflang,
  isPrivatePath,
  languageAlternates,
  localizeHref,
  localizedPath,
  splitLocale,
  templateLocales,
} from "@/lib/locale-path"

describe("localizedPath", () => {
  it("keeps English without a prefix", () => {
    expect(localizedPath("en", "/pricing")).toBe("/pricing")
    expect(localizedPath("en", "/")).toBe("/")
  })

  it("puts other languages under their prefix, the home page at the prefix itself", () => {
    expect(localizedPath("de", "/pricing")).toBe("/de/pricing")
    expect(localizedPath("fil", "/")).toBe("/fil")
  })
})

describe("languageAlternates", () => {
  it("names only the given languages, English always the default", () => {
    expect(languageAlternates("/guides/x", ["en", "de"])).toEqual({
      en: "/guides/x",
      de: "/de/guides/x",
      "x-default": "/guides/x",
    })
  })

  it("names every language's address and English as the default", () => {
    const links = languageAlternates("/faq")

    expect(links.en).toBe("/faq")
    expect(links.ar).toBe("/ar/faq")
    expect(links["x-default"]).toBe("/faq")
    // 23 languages and the default.
    expect(Object.keys(links)).toHaveLength(24)
  })

  it("names Filipino and Chinese by the codes search engines read, at their own addresses", () => {
    const links = languageAlternates("/faq")

    expect(links.tl).toBe("/fil/faq")
    expect(links["zh-Hans"]).toBe("/zh/faq")
    expect(links.fil).toBeUndefined()
    expect(links.zh).toBeUndefined()
    // Every code is two letters, with a script where one is named.
    expect(
      Object.keys(links).every((code) =>
        /^([a-z]{2}(-[A-Z][a-z]{3})?|x-default)$/.test(code)
      )
    ).toBe(true)
  })
})

describe("hasLanguageVersions", () => {
  it("covers localized pages, articles, template pages and the news feed", () => {
    for (const path of [
      "/pricing",
      "/guides/hiring-engineers",
      "/tests/sql",
      "/news/rss.xml",
    ]) {
      expect(hasLanguageVersions(path), path).toBe(true)
    }
  })

  it("leaves out pages with one address and private ones", () => {
    for (const path of [
      "/privacy",
      "/api-docs",
      "/companies",
      "/practice/history",
    ]) {
      expect(hasLanguageVersions(path), path).toBe(false)
    }
  })
})

describe("hreflang", () => {
  it("keeps a two-letter code and maps the others", () => {
    expect(hreflang("de")).toBe("de")
    expect(hreflang("fil")).toBe("tl")
    expect(hreflang("zh")).toBe("zh-Hans")
  })
})

describe("isLocalizedPath", () => {
  it("covers the listed pages and every article", () => {
    expect(isLocalizedPath("/tests")).toBe(true)
    expect(isLocalizedPath("/guides")).toBe(true)
    expect(isLocalizedPath("/guides/hiring-engineers")).toBe(true)
    expect(isLocalizedPath("/compare/testgorilla")).toBe(true)
  })

  it("leaves other pages with one address", () => {
    expect(isLocalizedPath("/tests/backend-developer")).toBe(false)
    expect(isLocalizedPath("/privacy")).toBe(false)
    expect(isLocalizedPath("/guides/../privacy")).toBe(false)
  })
})

describe("localizeHref", () => {
  it("keeps a link in the address's language when its target has that version", () => {
    expect(localizeHref("de", "/faq")).toBe("/de/faq")
    expect(localizeHref("de", "/")).toBe("/de")
    expect(localizeHref("fr", "/guides/hiring-engineers")).toBe(
      "/fr/guides/hiring-engineers"
    )
    expect(localizeHref("de", "/practice?q=sql#list")).toBe(
      "/de/practice?q=sql#list"
    )
  })

  it("leaves other targets, and links on a plain address, as they are", () => {
    expect(localizeHref("de", "/privacy")).toBe("/privacy")
    expect(localizeHref("de", "https://example.com")).toBe(
      "https://example.com"
    )
    expect(localizeHref(null, "/faq")).toBe("/faq")
  })
})

describe("templateLocales", () => {
  it("names English and the template's language, nothing for an English template", () => {
    expect(templateLocales("de")).toEqual(["en", "de"])
    expect(templateLocales("en")).toBe(false)
  })
})

describe("splitLocale", () => {
  it("finds the language and page of a localized address", () => {
    expect(splitLocale("/de/pricing")).toEqual({
      locale: "de",
      path: "/pricing",
    })
    expect(splitLocale("/fr")).toEqual({ locale: "fr", path: "/" })
    expect(splitLocale("/uk/practice/")).toEqual({
      locale: "uk",
      path: "/practice",
    })
  })

  it("passes a template page's language address to the page, which keeps only its template's", () => {
    expect(splitLocale("/de/tests/buchhalter")).toEqual({
      locale: "de",
      path: "/tests/buchhalter",
    })
    expect(splitLocale("/de/practice/buchhalter")).toEqual({
      locale: "de",
      path: "/practice/buchhalter",
    })
    expect(splitLocale("/de/tests/buchhalter/extra")).toBeNull()
    expect(splitLocale("/de/practice/buchhalter/start")).toBeNull()
  })

  it("leaves English's prefix, unknown prefixes and pages without language versions alone", () => {
    expect(splitLocale("/en/pricing")).toBeNull()
    expect(splitLocale("/xx/pricing")).toBeNull()
    expect(splitLocale("/de/companies")).toBeNull()
    expect(splitLocale("/de/practice/history/abc")).toBeNull()
    expect(splitLocale("/de/guides/hiring-engineers")).toEqual({
      locale: "de",
      path: "/guides/hiring-engineers",
    })
    expect(splitLocale("/pricing")).toBeNull()
  })
})

describe("isPrivatePath", () => {
  it("marks signed-in areas and personal links", () => {
    expect(isPrivatePath("/companies")).toBe(true)
    expect(isPrivatePath("/companies/1/interviews")).toBe(true)
    expect(isPrivatePath("/apply/abc")).toBe(true)
    expect(isPrivatePath("/practice/backend-developer/start")).toBe(true)
  })

  it("leaves public pages, and pages that only begin alike, public", () => {
    expect(isPrivatePath("/practice")).toBe(false)
    expect(isPrivatePath("/practice/backend-developer")).toBe(false)
    expect(isPrivatePath("/pricing")).toBe(false)
    expect(isPrivatePath("/settingsabc")).toBe(false)
  })
})
