import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { PageHeader } from "@/components/common/page-header"
import { SubtopicList } from "@/components/questions/subtopic-list"
import { TopicQuestionLimit } from "@/components/questions/topic-question-limit"
import { SignInPage } from "@/components/common/sign-in-page"
import { UseTemplate } from "@/components/templates/use-template"
import { serverFetch, signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Company } from "@/types/company"
import type { Template } from "@/types/superadmin"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"

export const generateMetadata = () => translatedTitle("templates", "title")

/** A template a company reviews before using it, laid out like a test page: its topics and
 * subtopics; its questions stay hidden until it's used. */
export default async function CompanyTemplatePage({
  params,
}: {
  params: Promise<{ companyId: string; templateId: string }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId, templateId } = await params
  const t = await getTranslations("templates")
  const [template, company] = await Promise.all([
    serverFetch<Template>(`/library/templates/${templateId}`),
    serverFetch<Company>(`/companies/companies/${companyId}`),
  ])

  if (!template) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        back={
          <BackLink href={`/companies/${companyId}/templates`} help="template">
            {t("title")}
          </BackLink>
        }
        title={
          // On phones the button goes under the title, across the page, as on other pages.
          <div className="flex items-start justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
            <h1 className="min-w-0 flex-1 font-heading text-3xl font-medium tracking-tight text-balance normal-case">
              {template.title}
            </h1>
            {/* Using a template creates a test: not for viewers. */}
            {company?.can_edit && (
              <UseTemplate templateId={templateId} companyId={companyId} />
            )}
          </div>
        }
      />

      <ul className={`${LIST_BOX} overflow-hidden`}>
        {template.topics.map((topic) => (
          <li
            key={topic.id}
            className={`flex items-center justify-between gap-6 p-4 ${ROW_HOVER} sm:p-6`}
          >
            <span className="max-w-3xl min-w-0 space-y-3">
              <span className="block text-lg font-medium">{topic.title}</span>
              <SubtopicList subtopics={topic.subtopics} />
            </span>
            <TopicQuestionLimit count={topic.question_count} limit={null} />
          </li>
        ))}
      </ul>
    </main>
  )
}
