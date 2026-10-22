import { readFile } from "node:fs/promises"
import path from "node:path"

import { describe, expect, it } from "vitest"

import { CONTENT_ROOT, type ContentFolder } from "@/constants/content"
import { DEFAULT_LOCALE } from "@/constants/i18n"
import { contentLanguages, contentPages, parseContent } from "@/lib/content"

// Rule 23's limits: search results cut longer titles and snippets.
const SEO_TITLE_MAX = 60
const DESCRIPTION_MAX = 155
const FOLDERS: ContentFolder[] = ["pages", "compare", "guides"]

/** Every article in every language it's written in, with its file's own text. */
async function everyFile() {
  const files = []

  for (const folder of FOLDERS) {
    for (const page of await contentPages(folder)) {
      for (const locale of await contentLanguages(folder, page.slug)) {
        const file =
          locale === DEFAULT_LOCALE
            ? path.join(CONTENT_ROOT, folder, `${page.slug}.md`)
            : path.join(CONTENT_ROOT, locale, folder, `${page.slug}.md`)
        const text = await readFile(file, "utf8")

        files.push({ file, text, page: parseContent(page.slug, text, locale) })
      }
    }
  }

  return files
}

describe("articles' front matter", () => {
  it("is complete and within the limits in every folder and language", async () => {
    const files = await everyFile()

    // English and at least one translation of each folder.
    expect(files.length).toBeGreaterThan(FOLDERS.length * 2)

    for (const { file, text, page } of files) {
      expect(text, file).toMatch(/^---\n([\s\S]*?\n)?title: "/)
      expect([...page.seoTitle].length, file).toBeLessThanOrEqual(
        SEO_TITLE_MAX
      )
      expect(page.description, file).not.toBe("")
      expect([...page.description].length, file).toBeLessThanOrEqual(
        DESCRIPTION_MAX
      )
      expect(page.updated, file).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      // The body starts with the title as its heading.
      expect(
        text.split("\n---\n")[1].trimStart().startsWith(`# ${page.title}\n`),
        file
      ).toBe(true)
    }
  })
})
