import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { ContentArticle } from "@/components/content/content-article"
import type { ContentFolder } from "@/constants/content"
import { contentLanguages, contentPage } from "@/lib/content"
import { pageMetadata } from "@/lib/site"
import type { PageHelpKey } from "@/types/page-help"

type Params = { params: Promise<{ slug: string }> }

// The metadata and the page of one content page, in the interface's language where translated.

async function metadata(folder: ContentFolder, slug: string, path: string) {
  const page = await contentPage(folder, slug, await getLocale())

  return page
    ? pageMetadata(
        page.seoTitle,
        page.description,
        path,
        await contentLanguages(folder, slug)
      )
    : {}
}

async function article(
  folder: ContentFolder,
  slug: string,
  path: string,
  pageKey: PageHelpKey,
  section?: { name: string; path: string }
) {
  const page = await contentPage(folder, slug, await getLocale())

  if (!page) {
    notFound()
  }

  return (
    <ContentArticle
      page={page}
      path={path}
      pageKey={pageKey}
      section={section}
    />
  )
}

/** A hub's article (content/guides/<slug>.md at /guides/<slug>), under the hub. */
export function hubArticleRoute(hub: "guides" | "compare") {
  return {
    generateMetadata: async ({ params }: Params) => {
      const { slug } = await params

      return metadata(hub, slug, `/${hub}/${slug}`)
    },
    Page: async ({ params }: Params) => {
      const { slug } = await params
      const t = await getTranslations(hub)

      return article(
        hub,
        slug,
        `/${hub}/${slug}`,
        hub === "guides" ? "guide" : "comparison",
        {
          name: t("title"),
          path: `/${hub}`,
        }
      )
    },
  }
}

/** A category page for companies searching the category (content/pages/<slug>.md at /<slug>),
 * with its guide's key. */
export function categoryRoute(slug: string, pageKey: PageHelpKey) {
  return {
    generateMetadata: () => metadata("pages", slug, `/${slug}`),
    Page: () => article("pages", slug, `/${slug}`, pageKey),
  }
}
