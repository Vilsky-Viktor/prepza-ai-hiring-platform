import { readdir, readFile } from "node:fs/promises"
import path from "node:path"

import { CONTENT_ROOT, type ContentFolder } from "@/constants/content"
import { DEFAULT_LOCALE, LOCALES } from "@/constants/i18n"
import { isLocale } from "@/lib/locale"

/** One page of the content: English in content/<folder>/<slug>.md, a translation in
 * content/<locale>/<folder>/<slug>.md. Its frontmatter, the language it's written in, and its
 * Markdown body without the body's own top heading (the page shows `title` as its heading). */
export type ContentPage = {
  slug: string
  language: string
  title: string
  seoTitle: string
  description: string
  updated: string
  body: string
}

// A slug as files are named; anything else (a path, a dot) is never read.
const SLUG = /^[a-z0-9-]+$/

/** The frontmatter's `key: "value"` lines and the text after it. */
export function parseContent(
  slug: string,
  text: string,
  language: string = DEFAULT_LOCALE
): ContentPage {
  const [, head = "", body = text] =
    text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/) ?? []
  const fields = Object.fromEntries(
    head.split("\n").flatMap((line) => {
      const found = line.match(/^(\w+):\s*"(.*)"\s*$/)

      return found ? [[found[1], found[2]]] : []
    })
  )

  return {
    slug,
    language,
    title: fields.title ?? slug,
    seoTitle: fields.seoTitle ?? fields.title ?? slug,
    description: fields.description ?? "",
    updated: fields.updated ?? "",
    body: body.replace(/^\s*# [^\n]*\n/, "").trim(),
  }
}

/** Where a page in `locale` is kept: English at the folder's top, a translation under its
 * language. */
function contentFile(folder: ContentFolder, slug: string, locale: string) {
  return locale === DEFAULT_LOCALE
    ? path.join(CONTENT_ROOT, folder, `${slug}.md`)
    : path.join(CONTENT_ROOT, locale, folder, `${slug}.md`)
}

async function readPage(folder: ContentFolder, slug: string, locale: string) {
  try {
    const text = await readFile(contentFile(folder, slug, locale), "utf8")

    return parseContent(slug, text, locale)
  } catch {
    return null
  }
}

/** A content page in `locale` (English by default), or English when it has no translation yet;
 * null when there's no page by that slug. */
export async function contentPage(
  folder: ContentFolder,
  slug: string,
  locale: string = DEFAULT_LOCALE
) {
  if (!SLUG.test(slug)) {
    return null
  }

  const translated =
    locale !== DEFAULT_LOCALE && isLocale(locale)
      ? await readPage(folder, slug, locale)
      : null

  return translated ?? readPage(folder, slug, DEFAULT_LOCALE)
}

/** Every page in a folder, in `locale` where translated, by title. */
export async function contentPages(
  folder: ContentFolder,
  locale: string = DEFAULT_LOCALE
) {
  const files = await readdir(path.join(CONTENT_ROOT, folder)).catch(() => [])
  const pages = await Promise.all(
    files
      .filter((file) => file.endsWith(".md"))
      .map((file) => contentPage(folder, file.slice(0, -3), locale))
  )

  return pages
    .filter((page): page is ContentPage => page !== null)
    .sort((a, b) => a.title.localeCompare(b.title, locale))
}

/** The languages a page is written in: English and every translation of it. */
export async function contentLanguages(folder: ContentFolder, slug: string) {
  const found = await Promise.all(
    LOCALES.map(async (locale) =>
      (await readPage(folder, slug, locale)) ? locale : null
    )
  )

  return found.filter((locale): locale is (typeof LOCALES)[number] => !!locale)
}
