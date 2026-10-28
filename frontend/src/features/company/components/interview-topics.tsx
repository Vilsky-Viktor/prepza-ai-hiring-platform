import { SubtopicList } from "@/components/common/subtopic-list"
import { TopicQuestionLimit } from "@/components/common/topic-question-limit"
import { TopicQuestions } from "@/components/common/topic-questions"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { languageOf } from "@/lib/locale"
import type { InterviewDetail } from "@/types/company"

/** An interview's topics, each with its questions and how many each candidate gets, in the
 * interview's `language`. Viewers read the questions; only owners and admins (`canEdit`) change
 * them. */
export function InterviewTopics({
  interviewId,
  language,
  topics,
  canEdit,
}: {
  interviewId: string
  language: string
  topics: InterviewDetail["topics"]
  canEdit: boolean
}) {
  const questionsPath = `/companies/interviews/${interviewId}/questions`

  if (topics.length === 0) {
    return null
  }

  return (
    <ul className={`${LIST_BOX} overflow-hidden`}>
      {topics.map((topic) => (
        // On phones the questions' button and their number take the line under the topic.
        <li
          key={topic.id}
          className={`flex items-center justify-between gap-6 p-4 ${ROW_HOVER} max-sm:flex-col max-sm:items-stretch max-sm:gap-6 max-sm:px-6 max-sm:py-8 sm:p-6`}
        >
          <span className="max-w-3xl min-w-0 space-y-3">
            <span {...languageOf(language)} className="block space-y-3">
              <span className="block text-lg font-medium">{topic.title}</span>
              <SubtopicList subtopics={topic.subtopics} />
            </span>
          </span>
          <span className="flex shrink-0 flex-col items-center gap-3 max-sm:flex-row max-sm:flex-wrap">
            <TopicQuestions
              title={topic.title}
              language={language}
              path={`/companies/interviews/${interviewId}/topics/${topic.id}/questions`}
              regeneratePath={canEdit ? questionsPath : undefined}
              wrongPath={canEdit ? questionsPath : undefined}
              reportsPath={canEdit ? questionsPath : undefined}
            />
            <TopicQuestionLimit
              count={topic.question_count}
              limit={topic.question_limit}
              limitPath={
                canEdit
                  ? `/companies/interviews/${interviewId}/topics/${topic.id}/limit`
                  : undefined
              }
            />
          </span>
        </li>
      ))}
    </ul>
  )
}
