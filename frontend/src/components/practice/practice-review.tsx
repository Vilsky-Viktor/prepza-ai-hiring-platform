"use client"

import { ScorecardMark } from "@/components/company/scorecard-review"
import { AnswerOptions } from "@/components/questions/answer-options"
import { AnswerPoints } from "@/components/questions/answer-points"
import { QuestionActions } from "@/components/questions/question-actions"
import { MultiChoiceTag } from "@/components/questions/multi-choice-tag"
import { QuestionText } from "@/components/questions/question-text"
import { VirtualList } from "@/components/common/virtual-list"
import { languageOf } from "@/lib/locale"
import type { ReviewItem } from "@/types/round"
import { LIST_BOX } from "@/config/lists"

/** A finished practice round's questions, laid out like a scorecard: each with right or wrong,
 * every option with the right one marked, and the talent's own pick. Under each, the talent
 * rates or reports it, as candidates do in a test; a reported wrong answer gets the question
 * checked and fixed. `sessionId` is the topic's section; `language` is the questions' own,
 * which can differ from the page's. */
export function PracticeReview({
  sessionId,
  items,
  language,
}: {
  sessionId: string
  items: ReviewItem[]
  language: string | null | undefined
}) {
  return (
    <VirtualList
      items={items}
      getKey={(item) => item.question_id}
      estimateSize={200}
      className={LIST_BOX}
      renderItem={(item) => (
        <div className="space-y-4 p-6 max-sm:py-8">
          {/* On phones whether it was right sits above the question, centered. */}
          <div className="flex items-start justify-between gap-8 max-sm:flex-col-reverse max-sm:items-center max-sm:gap-4">
            {/* A multi-answer question tagged as while it was played. */}
            <div
              className="min-w-0 space-y-3 max-sm:self-stretch"
              {...languageOf(language)}
            >
              {item.multi && <MultiChoiceTag />}
              <QuestionText text={item.text} className="text-lg font-light" />
            </div>
            <ScorecardMark item={item} />
          </div>
          <div {...languageOf(language)}>
            <AnswerOptions
              options={item.options.map((answer, index) => ({
                answer,
                correct: Boolean(item.correct_indexes?.includes(index)),
              }))}
              // None when unanswered or timed out: still a practice report.
              picked={item.answer?.picks ?? []}
              className="text-base"
            />
          </div>
          <AnswerPoints item={item} />
          <div className="max-sm:pt-4">
            <QuestionActions
              basePath={`/rounds/sessions/${sessionId}/questions/${item.question_id}`}
            />
          </div>
        </div>
      )}
    />
  )
}
