import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { DeleteTemplate } from "@/components/superadmin/delete-template"
import { TemplateAdditions } from "@/components/superadmin/template-additions"
import { BackLink } from "@/components/back-link"
import { EditableTitle } from "@/components/editable-title"
import { PageHeader } from "@/components/page-header"
import { SubtopicList } from "@/components/questions/subtopic-list"
import { TopicQuestions } from "@/components/questions/topic-questions"
import { DottedText } from "@/components/dot"
import { languageOf } from "@/lib/locale"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Addition } from "@/types/generation"
import type { PooledTemplate } from "@/types/superadmin"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"

export const generateMetadata = () => translatedTitle("superadmin", "templates")

/** One template: rename or delete it, check or re-generate its questions, and add more. */
export default async function TemplatePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("superadmin")
  const [template, addition] = await Promise.all([
    serverFetch<PooledTemplate>(`/library/superadmin/templates/${id}`),
    serverFetch<Addition>(
      `/generate/superadmin/templates/${id}/additions/latest`
    ),
  ])

  if (!template) {
    notFound()
  }

  const base = `/library/superadmin/templates/${id}`

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        back={
          <BackLink href="/superadmin/templates">{t("templates")}</BackLink>
        }
        title={
          // The actions on the title's line, "add questions" last; a run's progress goes on its
          // own line below.
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="min-w-0 flex-1">
              <EditableTitle title={template.title} path={`${base}/title`} />
            </div>
            <DeleteTemplate templateId={id} title={template.title} />
            {addition && (
              <TemplateAdditions
                templateId={id}
                short={template.short}
                initial={addition}
              />
            )}
          </div>
        }
      />

      <ul className={`${LIST_BOX} overflow-hidden`}>
        {template.topics.map((topic) => (
          // On phones the questions' button and count go under the subtopics, centered.
          <li
            key={topic.id}
            className={`flex items-center justify-between gap-6 p-4 ${ROW_HOVER} max-sm:flex-col max-sm:items-stretch max-sm:px-6 max-sm:py-8 sm:p-6`}
          >
            <span
              {...languageOf(template.language)}
              className="max-w-3xl min-w-0 space-y-3"
            >
              <span className="block text-lg font-medium">{topic.title}</span>
              <SubtopicList subtopics={topic.subtopics} />
            </span>
            <span className="flex shrink-0 flex-col items-center gap-3 max-sm:flex-row max-sm:flex-wrap max-sm:justify-center max-sm:gap-4">
              <TopicQuestions
                title={topic.title}
                language={template.language}
                path={`${base}/topics/${topic.id}/questions`}
                regeneratePath={`/generate/superadmin/templates/${id}/questions`}
                wrongPath={`${base}/questions`}
                reportsPath={`${base}/questions`}
              />
              <p
                className="text-sm whitespace-nowrap text-muted-foreground tabular-nums"
                data-testid="pool-counts"
              >
                <DottedText
                  text={t("poolCounts", {
                    practice: topic.practice_count,
                    company: topic.company_count,
                  })}
                />
              </p>
            </span>
          </li>
        ))}
      </ul>
    </main>
  )
}
