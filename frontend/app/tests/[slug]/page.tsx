import Link from "next/link"
import { notFound, permanentRedirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { FaqList } from "@/components/faq-list"
import { JsonLd } from "@/components/json-ld"
import { PageHeader } from "@/components/page-header"
import { SubtopicList } from "@/components/questions/subtopic-list"
import { SampleQuestions } from "@/components/tests/sample-questions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DEFAULT_LOCALE } from "@/constants/i18n"
import { ROLE_PAGE_FAQ } from "@/constants/role-tests"
import { publicFetch } from "@/lib/server-api"
import { textDirection } from "@/lib/locale"
import { localizedPath, templateLocales } from "@/lib/locale-path"
import { pageMetadata, siteUrl, urlLocale } from "@/lib/site"
import { breadcrumbData } from "@/lib/structured-data"
import {
  countryCatalog,
  faqPath,
  priceValues,
  visitorCatalog,
} from "@/lib/catalog"
import type { FaqItem } from "@/types/help"
import type { SampleQuestion, Template } from "@/types/superadmin"
import { LIST_BOX } from "@/constants/lists"
import { PageKey } from "@/components/page-key"

type Params = { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: Params) {
  const { slug } = await params
  const t = await getTranslations("tests")
  const [template, catalog] = await Promise.all([
    publicFetch<Template>(`/library/templates/${slug}`),
    countryCatalog(),
  ])

  if (!template) {
    return {}
  }

  return {
    ...(await pageMetadata(
      t("pageTitle", { role: template.title }),
      t("pageDescription", {
        role: template.title,
        count: template.topic_count,
        ...(await priceValues(catalog)),
      }),
      `/tests/${template.slug ?? template.id}`,
      templateLocales(template.language)
    )),
    // Kept out of search results when the API says it's too thin or a near-duplicate.
    robots: template.indexable ? undefined : { index: false },
  }
}

/** A role's skills test for companies hiring for it, made from its template: what it checks,
 * the way to test candidates, and sample questions (which also answer candidates' searches,
 * with a link to free practice). Its address is the template's slug. */
export default async function RoleTestPage({ params }: Params) {
  const { slug: key } = await params
  const t = await getTranslations("tests")
  const tLevel = await getTranslations("templates.levels")
  // Asked together: the template, the price per candidate in the visitor's currency, and the
  // site FAQ's answers to what companies ask before testing candidates, in the page's language
  // and with today's prices (left out while prices can't be read: rounds refuses).
  const [template, catalog, answers] = await Promise.all([
    publicFetch<Template>(`/library/templates/${key}`),
    visitorCatalog(),
    faqPath()
      .then((path) => publicFetch<FaqItem[]>(path))
      .catch(() => null),
  ])

  const locale = await urlLocale()

  // Links stay in the language of the page's address (/de/tests/… leads to /de/…).
  const at = (path: string) => localizedPath(locale ?? DEFAULT_LOCALE, path)

  // Only English and the template's own language have this page.
  if (!template || (locale && locale !== template.language)) {
    notFound()
  }

  if (template.slug && key !== template.slug) {
    permanentRedirect(at(`/tests/${template.slug}`))
  }

  const slug = template.slug ?? template.id
  const prices = await priceValues(catalog)
  const questions =
    (await publicFetch<SampleQuestion[]>(
      `/library/templates/${slug}/sample`
    )) ?? []
  const faq = (answers ?? []).filter((item) => ROLE_PAGE_FAQ.includes(item.key))

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-6 py-12">
      <PageKey page="test" />
      <JsonLd
        data={breadcrumbData(siteUrl(), [
          { name: "prepza", path: at("/") },
          { name: t("title"), path: at("/tests") },
          { name: template.title, path: at(`/tests/${slug}`) },
        ])}
      />
      <PageHeader
        back={<BackLink href="/tests">{t("title")}</BackLink>}
        tags={
          <>
            <Badge variant="outline" className="h-7 px-3 text-sm font-light">
              {tLevel(template.level)}
            </Badge>
            <Badge
              variant="outline"
              className="h-7 px-3 text-sm font-light uppercase"
            >
              {template.language}
            </Badge>
          </>
        }
        title={
          <h1 className="font-heading text-3xl font-medium tracking-tight text-balance normal-case">
            {t("heading", { role: template.title })}
          </h1>
        }
      />
      <div className="space-y-6">
        <p className="text-lg text-muted-foreground">{t("lead", prices)}</p>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            className="h-12 px-6 text-base"
            render={<Link href={at("/")} />}
            nativeButton={false}
          >
            {t("create")}
          </Button>
          <Button
            variant="outline"
            className="h-12 px-6 text-base"
            render={<Link href={at(`/practice/${slug}`)} />}
            nativeButton={false}
          >
            {t("practise")}
          </Button>
        </div>
      </div>

      <section className="space-y-4">
        <h2 className="font-heading text-2xl font-medium">{t("topics")}</h2>
        <ul
          lang={template.language}
          dir={textDirection(template.language)}
          className={LIST_BOX}
        >
          {template.topics.map((topic) => (
            <li
              key={topic.id}
              className="space-y-3 p-4 max-sm:px-6 max-sm:py-8 sm:p-6"
            >
              <span className="block text-lg font-medium">{topic.title}</span>
              <SubtopicList subtopics={topic.subtopics} />
            </li>
          ))}
        </ul>
      </section>

      {questions.length > 0 && (
        <SampleQuestions questions={questions} language={template.language} />
      )}

      {faq.length > 0 && (
        <section className="space-y-4">
          <h2 className="font-heading text-2xl font-medium">{t("faq")}</h2>
          <FaqList items={faq} />
        </section>
      )}
    </main>
  )
}
