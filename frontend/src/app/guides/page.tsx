import { getLocale, getTranslations } from "next-intl/server"

import { ContentList } from "@/components/content/content-list"
import { contentPages } from "@/lib/content"
import { pageMetadata } from "@/lib/site"
import { PageKey } from "@/components/page-key"

export async function generateMetadata() {
  const t = await getTranslations("guides")

  return pageMetadata(t("title"), t("intro"), "/guides", true)
}

/** The guides hub: every page in content/guides, by title. */
export default async function HubPage() {
  const t = await getTranslations("guides")
  // In the interface's language where translated.
  const pages = await contentPages("guides", await getLocale())

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageKey page="guides" />
      <div className="space-y-2">
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">{t("intro")}</p>
      </div>
      <ContentList pages={pages} base="/guides" />
    </main>
  )
}
