import type { Metadata } from "next"
import { headers } from "next/headers"
import { getLocale, getTranslations } from "next-intl/server"

import { DEFAULT_LOCALE, LOCALES, type Locale } from "@/constants/i18n"
import {
  PREVIEW_TITLE_MAX,
  PREVIEW_UNSUPPORTED,
} from "@/constants/preview-image"
import { CATEGORY_PAGES } from "@/constants/content"
import { LOCALE_HEADER, LOCALIZED_ARTICLE, SITE_NAME } from "@/constants/seo"
import { hreflang, languageAlternates, localizedPath } from "@/lib/locale-path"
import { previewSignature } from "@/lib/preview-signature"

/** The site's public address, for absolute links in metadata, robots.txt and the sitemap. */
export function siteUrl() {
  return process.env.SITE_URL ?? "http://localhost:8090"
}

/** The link-preview picture at the site's own address (Next.js would otherwise name the dev
 * server's internal one, and a page's openGraph would drop it): the page's title under the logo
 * (app/preview/route.tsx), or the site's own (app/opengraph-image.tsx) without a title or in a
 * language the picture can't draw. */
export function previewImage(title?: string, locale: string = DEFAULT_LOCALE) {
  const drawn = title && !PREVIEW_UNSUPPORTED.includes(locale as Locale)
  const shown = (title ?? "").slice(0, PREVIEW_TITLE_MAX)
  // Signed, so the picture route draws only titles our own pages name.
  const query = new URLSearchParams({
    title: shown,
    lang: locale,
    sig: previewSignature(shown, locale),
  })
  const url = drawn
    ? `${siteUrl()}/preview?${query}`
    : `${siteUrl()}/opengraph-image`

  // The picture shows the title under the logo, or the site's own promise under it.
  return [{ url, width: 1200, height: 630, alt: title ?? SITE_NAME }]
}

/** A language as link previews name it (og:locale): its hreflang code, "_" for "-". */
export function ogLocale(locale: string) {
  return hreflang(locale).replace("-", "_")
}

/** A page's other languages for link previews (og:locale:alternate). */
function otherOgLocales(locales: readonly string[], shown: string) {
  return locales.filter((other) => other !== shown).map(ogLocale)
}

/** The language of the address the page was asked for (/de/pricing gives de), or null for a
 * plain address. */
export async function urlLocale() {
  return (await headers()).get(LOCALE_HEADER)
}

/** A page's title in the interface language, for its generateMetadata. */
export async function translatedTitle(
  namespace: string,
  key: string
): Promise<Metadata> {
  const t = await getTranslations(namespace)

  return { title: t(key) }
}

/** The title a page's preview picture draws: lowercase like the site's titles; articles and the
 * API docs keep their capitals (names such as TestGorilla, EU or API). */
function pictureTitle(title: string, path: string, locale: string) {
  const capitals =
    LOCALIZED_ARTICLE.test(path) ||
    CATEGORY_PAGES.includes(path.slice(1)) ||
    path === "/api-docs"

  return capitals ? title : title.toLocaleLowerCase(locale)
}

/** A public page's own description and canonical address, also used in its link previews. A
 * localized page (lib/locale-path.ts isLocalizedPath) names the address of the language it's
 * served in as canonical, and every language's address for hreflang; `localized` as a list
 * names only those languages (an article's translations), and a language outside it has the
 * English address as canonical. */
export async function pageMetadata(
  title: string,
  description: string,
  path: string,
  localized: boolean | readonly string[] = false
): Promise<Metadata> {
  const locale = (await urlLocale()) ?? DEFAULT_LOCALE
  const languages = localized === true ? undefined : localized || undefined
  const own = localized === true || (languages ?? []).includes(locale)
  const canonical = own ? localizedPath(locale, path) : path
  // The language it's shown in: its address's, English for an untranslated article, the
  // interface's on a page with one address.
  const shown = localized ? (own ? locale : DEFAULT_LOCALE) : await getLocale()

  return {
    title,
    description,
    alternates: {
      canonical,
      languages: localized ? languageAlternates(path, languages) : undefined,
    },
    // A page's openGraph replaces the layout's, so the shared fields are repeated here; Next.js
    // fills its title and description from the page's own.
    openGraph: {
      siteName: SITE_NAME,
      type: "website",
      url: canonical,
      locale: ogLocale(shown),
      alternateLocale: localized
        ? otherOgLocales(languages ?? LOCALES, shown)
        : undefined,
      images:
        path === "/"
          ? previewImage()
          : previewImage(pictureTitle(title, path, locale), locale),
    },
  }
}
