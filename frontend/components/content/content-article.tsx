import { cn } from "cn"
import { getLocale, getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { Markdown } from "@/components/content/markdown"
import { StartCard } from "@/components/content/start-card"
import { JsonLd } from "@/components/json-ld"
import { PageKey } from "@/components/page-key"
import { DEFAULT_LOCALE } from "@/constants/i18n"
import type { ContentPage } from "@/lib/content"
import { formatDay } from "@/lib/format"
import { textDirection } from "@/lib/locale"
import { localizeHref } from "@/lib/locale-path"
import { endsWithQuestionMark } from "@/lib/question-mark"
import { previewImage, siteUrl, urlLocale } from "@/lib/site"
import { articleData, breadcrumbData } from "@/lib/structured-data"
import type { PageHelpKey } from "@/types/page-help"

/** One content page (a category page, a comparison or a guide): its heading, date and text,
 * then the way to a first test, in the language it's written in (English where it has no
 * translation yet, with a note). `section` is the hub it belongs to, for the back link and the
 * breadcrumb; `pageKey`, its guide's key. */
export async function ContentArticle({
  page,
  path,
  pageKey,
  section,
}: {
  page: ContentPage
  path: string
  pageKey: PageHelpKey
  section?: { name: string; path: string }
}) {
  const t = await getTranslations("content")
  const locale = await getLocale()
  const address = await urlLocale()
  // The breadcrumb names the addresses in the page's own language.
  const steps = [
    { name: "prepza", path: "/" },
    ...(section ? [section] : []),
    { name: page.title, path },
  ].map((step) => ({ ...step, path: localizeHref(address, step.path) }))

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageKey page={pageKey} />
      <JsonLd
        data={[
          articleData(siteUrl(), {
            ...page,
            // Its canonical address: the English one while it isn't translated.
            path:
              page.language === (address ?? DEFAULT_LOCALE)
                ? localizeHref(address, path)
                : path,
            // The page's link preview picture (lib/site.ts pageMetadata).
            image: previewImage(page.seoTitle, address ?? DEFAULT_LOCALE)[0]
              .url,
          }),
          breadcrumbData(siteUrl(), steps),
        ]}
      />
      <header className="mx-auto max-w-5xl space-y-4">
        {/* The way back beside the title, as on the app's pages: to the article's section, or
            home for a page without one. */}
        <div className="relative">
          {section ? (
            <BackLink href={section.path}>{section.name}</BackLink>
          ) : (
            <BackLink href="/">{null}</BackLink>
          )}
          <h1
            className={cn(
              "font-heading text-4xl font-medium tracking-tight text-balance normal-case",
              endsWithQuestionMark(page.title) && "no-dot"
            )}
          >
            {page.title}
          </h1>
        </div>
        <p className="text-lg text-muted-foreground">{page.description}</p>
        <p className="text-sm text-muted-foreground">
          {page.language !== locale && (
            <span className="block pb-2">{t("englishOnly")}</span>
          )}
          {/* The date line in italics. */}
          <span className="italic">
            {t("updated")}{" "}
            <time dateTime={page.updated}>
              {/* At midday UTC, so the day is the same in any time zone. */}
              {formatDay(page.updated, locale)}
            </time>
          </span>
        </p>
      </header>
      <article
        lang={page.language}
        dir={textDirection(page.language)}
        className="mx-auto max-w-5xl space-y-5"
      >
        <Markdown text={page.body} />
      </article>
      <StartCard />
    </main>
  )
}
