import type { MetadataRoute } from "next"

import { PUBLIC_TIMEOUT_MS } from "@/constants/api"
import { CATEGORY_PAGES } from "@/constants/content"
import { DEFAULT_LOCALE, LOCALES } from "@/constants/i18n"
import { LOCALIZED_PATHS, PUBLIC_PATHS } from "@/constants/seo"
import { contentLanguages, contentPage, contentPages } from "@/lib/content"
import {
  languageAlternates,
  localizedPath,
  templateLocales,
} from "@/lib/locale-path"
import { publicFetch } from "@/lib/server-api"
import { siteUrl } from "@/lib/site"

// The API's largest page, and how many pages of templates the sitemap reads at most.
const PAGE = 100
const MAX_PAGES = 50

type Template = {
  id: string
  slug: string | null
  language: string
  updated_at: string
  indexable: boolean
}

/** Every template, read from the public list a page at a time. A page that can't be read (an
 * error, no answer in time) fails the whole sitemap rather than leaving the role tests out:
 * search engines keep the last one and ask again, where a partial one would drop those pages. */
async function templates(): Promise<Template[]> {
  const rows: Template[] = []

  for (let page = 0; page < MAX_PAGES; page++) {
    const path = `/library/templates?offset=${page * PAGE}&limit=${PAGE}`
    const batch = await publicFetch<Template[]>(path, {
      locale: DEFAULT_LOCALE,
      fresh: true,
    })

    if (batch === null) {
      throw new Error(`The sitemap couldn't read ${path}`)
    }

    rows.push(...batch)

    if (batch.length < PAGE) {
      break
    }
  }

  return rows
}

/** The day of the newest news post, for the news page's date; none without posts. */
async function latestNews(): Promise<string | undefined> {
  const response = await fetch(
    `${process.env.API_URL}/api/library/news?offset=0&limit=1`,
    { cache: "no-store", signal: AbortSignal.timeout(PUBLIC_TIMEOUT_MS) }
  ).catch(() => null)

  if (!response?.ok) {
    return undefined
  }

  const [latest]: { published_on: string }[] = await response.json()

  return latest?.published_on
}

// The legal pages, at the rounds service's address of each one's text.
const LEGAL_PATHS = ["/privacy", "/terms", "/dpa"]

/** The day a legal page was last updated, by its path; none when the API doesn't answer. */
async function legalUpdated(): Promise<Record<string, string | undefined>> {
  const days = await Promise.all(
    LEGAL_PATHS.map(async (path) => {
      const response = await fetch(
        `${process.env.API_URL}/api/rounds/help/legal${path}`,
        { cache: "no-store", signal: AbortSignal.timeout(PUBLIC_TIMEOUT_MS) }
      ).catch(() => null)

      if (!response?.ok) {
        return [path, undefined]
      }

      // The latest version's day: the page has said it since.
      const document: { current: string } = await response.json()

      return [path, document.current]
    })
  )

  return Object.fromEntries(days)
}

// Articles in each content folder, by the address they live at.
const ARTICLES = [
  { folder: "pages", base: "" },
  { folder: "compare", base: "/compare" },
  { folder: "guides", base: "/guides" },
] as const

/** Every article in each language it's written in, each naming its translations, with the
 * date that language's text was last updated. */
async function articles(site: string) {
  const absolute = (links: Record<string, string>) =>
    Object.fromEntries(
      Object.entries(links).map(([locale, path]) => [locale, `${site}${path}`])
    )
  const lists = await Promise.all(
    ARTICLES.map(async ({ folder, base }) => {
      const pages = await contentPages(folder)

      return Promise.all(
        pages.map(async (page) => {
          const path = `${base}/${page.slug}`
          const languages = await contentLanguages(folder, page.slug)
          // Each language's own date: a translation may be updated apart from the English.
          const dates = await Promise.all(
            languages.map(
              async (locale) =>
                (await contentPage(folder, page.slug, locale))?.updated
            )
          )

          return languages.map((locale, index) => ({
            url: `${site}${localizedPath(locale, path)}`,
            lastModified: dates[index] || undefined,
            alternates: {
              languages: absolute(languageAlternates(path, languages)),
            },
          }))
        })
      )
    })
  )

  return lists.flat(2)
}

/** The public pages (those in every language with each language's address; the news page with
 * its newest post's day, the legal pages with their last update), the articles in their
 * languages with their dates, and the role test page and free practice page of each template
 * the API marks indexable. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = siteUrl()
  const absolute = (links: Record<string, string>) =>
    Object.fromEntries(
      Object.entries(links).map(([locale, path]) => [locale, `${site}${path}`])
    )
  // The category pages are articles: listed with their translations below.
  const everyLanguage = LOCALIZED_PATHS.filter(
    (path) => !CATEGORY_PAGES.includes(path.slice(1))
  )
  const [rows, written, news, legal] = await Promise.all([
    templates(),
    articles(site),
    latestNews(),
    legalUpdated(),
  ])

  return [
    // A page in every language is listed once per language, each naming all of them.
    ...everyLanguage.flatMap((path) =>
      LOCALES.map((locale) => ({
        url: `${site}${localizedPath(locale, path)}`,
        lastModified: path === "/news" ? news : undefined,
        alternates: { languages: absolute(languageAlternates(path)) },
      }))
    ),
    ...PUBLIC_PATHS.filter((path) => !LOCALIZED_PATHS.includes(path)).map(
      (path) => ({ url: `${site}${path}`, lastModified: legal[path] })
    ),
    ...written,
    // A template's pages in English and in its language, each naming the other.
    ...rows
      .filter((row) => row.indexable)
      .flatMap((row) => {
        const languages = templateLocales(row.language)

        return ["/tests", "/practice"].flatMap((base) => {
          const path = `${base}/${row.slug ?? row.id}`
          const alternates = languages
            ? { languages: absolute(languageAlternates(path, languages)) }
            : undefined

          return (languages || [DEFAULT_LOCALE]).map((locale) => ({
            url: `${site}${localizedPath(locale, path)}`,
            lastModified: row.updated_at,
            alternates,
          }))
        })
      }),
  ]
}
