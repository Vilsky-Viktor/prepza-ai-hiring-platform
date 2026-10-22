import { describe, expect, it } from "vitest"

import {
  contentLanguages,
  contentPage,
  contentPages,
  parseContent,
} from "@/lib/content"

const TEXT = `---
title: "Hiring engineers"
seoTitle: "How to hire engineers"
description: "A process from job description to offer."
updated: "2026-10-07"
---

# Hiring engineers

Start with the role.
`

describe("parseContent", () => {
  it("reads the frontmatter and drops the body's own top heading", () => {
    expect(parseContent("hiring-engineers", TEXT)).toEqual({
      slug: "hiring-engineers",
      language: "en",
      title: "Hiring engineers",
      seoTitle: "How to hire engineers",
      description: "A process from job description to offer.",
      updated: "2026-10-07",
      body: "Start with the role.",
    })
  })

  it("falls back to the title, then the slug, when fields are missing", () => {
    const page = parseContent("plain", "Just text.")

    expect(page.title).toBe("plain")
    expect(page.seoTitle).toBe("plain")
    expect(page.body).toBe("Just text.")
  })
})

describe("contentPage", () => {
  it("reads a page from the content folder", async () => {
    const page = await contentPage("pages", "pre-employment-testing")

    expect(page?.title).toBeTruthy()
  })

  it("reads a translation when there is one, else falls back to English", async () => {
    const english = await contentPage("guides", "hiring-engineers")
    // A language code that isn't one of the site's: never read, English instead.
    const unknown = await contentPage("guides", "hiring-engineers", "xx")

    expect(english?.language).toBe("en")
    expect(unknown?.language).toBe("en")
    expect(unknown?.title).toBe(english?.title)
  })

  it("never reads outside the folder or a missing page", async () => {
    expect(await contentPage("guides", "../pages/ai-interviews")).toBeNull()
    expect(await contentPage("guides", "no-such-guide")).toBeNull()
  })
})

describe("contentPages", () => {
  it("lists every page of a folder", async () => {
    const pages = await contentPages("compare")

    expect(pages.length).toBeGreaterThan(0)
    expect(pages.every((page) => page.slug && page.title)).toBe(true)
  })
})

describe("contentLanguages", () => {
  it("names English and the translations that exist", async () => {
    const languages = await contentLanguages("guides", "hiring-engineers")

    expect(languages[0]).toBe("en")

    for (const locale of languages) {
      expect(
        (await contentPage("guides", "hiring-engineers", locale))?.language
      ).toBe(locale)
    }
  })
})
