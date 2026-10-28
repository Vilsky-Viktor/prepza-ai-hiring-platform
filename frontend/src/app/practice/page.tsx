import { cookies } from "next/headers"
import { getTranslations } from "next-intl/server"

import {
  TemplateBrowser,
  type TemplateSearchParams,
} from "@/features/templates/components/template-browser"
import { TOKEN_COOKIE } from "@/config/auth"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { localizedPath } from "@/lib/locale-path"
import { serverFetch } from "@/lib/server-api"
import { pageMetadata, urlLocale } from "@/lib/site"
import { PUBLIC_TEMPLATES_PATH } from "@/config/lists"
import { PageKey } from "@/components/common/page-key"
import type { PracticeStatus } from "@/types/round"

export async function generateMetadata() {
  const t = await getTranslations("practice")

  return pageMetadata(t("title"), t("intro"), "/practice", true)
}

/** The free practice library: every template, searched and filtered like the companies' list.
 * Public, for search engines; advertised as practice, never as a real interview. */
export default async function PracticePage({
  searchParams,
}: {
  searchParams: Promise<TemplateSearchParams>
}) {
  const t = await getTranslations("practice")
  // Signed in: which tests the talent started or finished, as the API decides.
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const statuses = signedIn
    ? await serverFetch<PracticeStatus[]>("/rounds/practice/statuses")
    : null
  const browser = await TemplateBrowser({
    // A search stays in the language of the address it started on.
    base: localizedPath((await urlLocale()) ?? DEFAULT_LOCALE, "/practice"),
    listPath: PUBLIC_TEMPLATES_PATH,
    params: await searchParams,
    openBase: "/practice",
    bySlug: true,
    statuses: statuses ?? undefined,
  })

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageKey page="practice" />
      <div className="space-y-2">
        <h1 className="font-heading text-3xl font-medium tracking-tight">
          {t("title")}
        </h1>
        <p className="text-base text-muted-foreground">{t("intro")}</p>
      </div>
      {browser}
    </main>
  )
}
