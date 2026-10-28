import { InfoIcon } from "lucide-react"
import { cookies } from "next/headers"
import { notFound, permanentRedirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { CornerSign } from "@/components/common/corner-sign"
import { JsonLd } from "@/components/common/json-ld"
import { PageHeader } from "@/components/common/page-header"
import { HireWithTemplate } from "@/components/practice/hire-with-template"
import { PracticeActions } from "@/components/practice/practice-actions"
import { SubtopicList } from "@/components/questions/subtopic-list"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { TOKEN_COOKIE } from "@/config/auth"
import { DEFAULT_LOCALE } from "@/config/i18n"
import { textDirection } from "@/lib/locale"
import { localizedPath, templateLocales } from "@/lib/locale-path"
import { hasMessage } from "@/lib/messages"
import { pageMetadata, siteUrl, urlLocale } from "@/lib/site"
import { publicFetch, serverFetch } from "@/lib/server-api"
import { breadcrumbData } from "@/lib/structured-data"
import type { PracticeSize, PracticeTopicProgress } from "@/types/round"
import type { Template } from "@/types/superadmin"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { PageKey } from "@/components/common/page-key"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("practice")
  const tLevel = await getTranslations("templates.levels")
  const template = await publicFetch<Template>(`/library/templates/${id}`)

  if (!template) {
    return {}
  }

  return {
    ...(await pageMetadata(
      t("pageTitle", { title: template.title }),
      t("pageDescription", {
        title: template.title,
        level: hasMessage(tLevel, template.level)
          ? tLevel(template.level)
          : template.level,
        count: template.topic_count,
      }),
      `/practice/${template.slug ?? template.id}`,
      templateLocales(template.language)
    )),
    // Kept out of search results when the API says it's too thin or a near-duplicate.
    robots: template.indexable ? undefined : { index: false },
  }
}

/** One free practice test, public for search engines: the role, its level and language, and
 * the topics it covers. Its questions are never shown here. Its address is the template's slug;
 * an old address by id moves there for good. */
export default async function PracticeTestPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: key } = await params
  const t = await getTranslations("practice")
  const tLevel = await getTranslations("templates.levels")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const template = await publicFetch<Template>(`/library/templates/${key}`)

  const locale = await urlLocale()

  // Links stay in the language of the page's address (/de/practice/… leads to /de/…).
  const at = (path: string) => localizedPath(locale ?? DEFAULT_LOCALE, path)

  // Only English and the template's own language have this page.
  if (!template || (locale && locale !== template.language)) {
    notFound()
  }

  if (template.slug && key !== template.slug) {
    permanentRedirect(at(`/practice/${template.slug}`))
  }

  const id = template.id
  const [size, progress] = await Promise.all([
    publicFetch<PracticeSize>(`/rounds/practice/${id}/size`),
    // The talent's latest score on each topic; nothing before their first round.
    signedIn
      ? serverFetch<PracticeTopicProgress[]>(`/rounds/practice/${id}/progress`)
      : null,
  ])

  const reached = new Map((progress ?? []).map((item) => [item.topic_id, item]))

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageKey page="practiceTest" />
      <JsonLd
        data={breadcrumbData(siteUrl(), [
          { name: "prepza", path: at("/") },
          { name: t("title"), path: at("/practice") },
          {
            name: template.title,
            path: at(`/practice/${template.slug ?? id}`),
          },
        ])}
      />
      <PageHeader
        back={<BackLink href="/practice">{t("title")}</BackLink>}
        // The level and language under the title; on phones the actions come after them, on a
        // line of their own, centered.
        title={
          <div className="flex items-start justify-between gap-4 max-sm:flex-wrap">
            <div className="min-w-0 flex-1 space-y-2">
              <h1 className="font-heading text-3xl font-medium tracking-tight text-balance normal-case">
                {template.title}
              </h1>
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant="outline"
                  className="h-7 px-3 text-sm font-light"
                >
                  {hasMessage(tLevel, template.level)
                    ? tLevel(template.level)
                    : template.level}
                </Badge>
                <Badge
                  variant="outline"
                  className="h-7 px-3 text-sm font-light uppercase"
                >
                  {template.language}
                </Badge>
              </div>
            </div>
            <div className="max-sm:flex max-sm:basis-full max-sm:justify-center max-sm:pt-2">
              <PracticeActions
                templateId={id}
                startLabel={t("start")}
                timings={size?.timings ?? []}
              />
            </div>
          </div>
        }
      />

      {/* One full-width card: the note on gray with its sign in the corner, as the info card's,
          continued by a round's length on the transparent part at the end. */}
      <div className="flex flex-wrap items-stretch overflow-hidden rounded-xl border text-base text-muted-foreground">
        <div className="relative flex flex-1 items-center bg-surface p-5 ps-20">
          <CornerSign>
            <InfoIcon className="text-primary" />
          </CornerSign>
          <p>{t("about")}</p>
        </div>
        {size && (
          // On phones on its own line, centered, in larger type.
          <p className="flex items-center px-5 py-4 max-sm:basis-full max-sm:justify-center max-sm:text-xl">
            {t("questions", { count: size.questions })}
          </p>
        )}
      </div>

      <ul
        lang={template.language}
        dir={textDirection(template.language)}
        className={`${LIST_BOX} overflow-hidden`}
      >
        {template.topics.map((topic) => {
          const step = reached.get(topic.id)

          return (
            <li
              key={topic.id}
              className={`p-4 ${ROW_HOVER} max-sm:px-6 max-sm:py-8 sm:p-6`}
            >
              <span className="block min-w-0 space-y-3">
                <span className="block text-lg font-medium">{topic.title}</span>
                <SubtopicList subtopics={topic.subtopics} />
                {/* Signed in: empty until the talent's first round, then how far their latest
                    round got on the topic. */}
                {signedIn && (
                  <span className="flex items-center gap-4">
                    <Progress
                      aria-label={topic.title}
                      value={step ? (step.answered / step.total) * 100 : 0}
                      className="flex-1"
                    />
                    <span className="shrink-0 text-base text-muted-foreground tabular-nums">
                      {step ? `${step.answered} / ${step.total}` : "—"}
                    </span>
                  </span>
                )}
              </span>
            </li>
          )
        })}
      </ul>

      {/* Visitors who hire for this role can create an interview for their own candidates. */}
      <HireWithTemplate templateId={template.id} />
    </main>
  )
}
