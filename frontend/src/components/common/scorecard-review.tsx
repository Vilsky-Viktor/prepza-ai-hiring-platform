"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { gradeTone } from "@/lib/grade-tone"
import { AnswerOptions } from "@/components/common/answer-options"
import { AnswerPoints } from "@/components/common/answer-points"
import { InlineText } from "@/components/common/inline-text"
import { MultiChoiceTag } from "@/components/common/multi-choice-tag"
import { QuestionText } from "@/components/common/question-text"
import { VirtualList } from "@/components/common/virtual-list"
import { languageOf } from "@/lib/locale"
import { verdict } from "@/lib/rounds"
import type { ReviewItem } from "@/types/round"
import { LIST_BOX } from "@/config/lists"
import { WARNING_TONE } from "@/config/tones"
import { Dot } from "@/components/common/dot"

/** A section's questions as the candidate answered them; the questions and options in the
 * interview's `language`, the marks and signals in the page's. */
export function ScorecardReview({
  items,
  language,
}: {
  items: ReviewItem[]
  language: string
}) {
  return (
    <VirtualList
      items={items}
      getKey={(item) => item.question_id}
      estimateSize={160}
      className={LIST_BOX}
      renderItem={(item) => (
        <div className="space-y-4 p-6 max-sm:py-8">
          {/* On phones whether it was right sits above the question, centered. */}
          <div className="flex items-start justify-between gap-4 max-sm:flex-col-reverse max-sm:items-center">
            {/* A multi-answer question tagged as while it was played. */}
            <div className="min-w-0 space-y-3 max-sm:self-stretch">
              {item.multi && <MultiChoiceTag />}
              <div {...languageOf(language)}>
                <QuestionText text={item.text} className="text-lg font-light" />
              </div>
            </div>
            <ScorecardMark item={item} />
          </div>
          <ScorecardAnswer item={item} language={language} />
          <ScorecardSignals item={item} />
        </div>
      )}
    />
  )
}

export function ScorecardMark({ item }: { item: ReviewItem }) {
  const t = useTranslations("scorecard")
  const rounds = useTranslations("rounds")
  const answer = item.answer

  // Unanswered and timed-out questions count as wrong.
  if (!answer || answer.timed_out) {
    return (
      <span
        data-verdict={answer ? "timeOut" : "notAnswered"}
        className={cn("shrink-0 text-lg font-light", gradeTone(false))}
      >
        {answer ? t("timeOut") : rounds("notAnswered")}
      </span>
    )
  }

  const shown = verdict(answer.correct, answer.score)

  return (
    <span
      data-verdict={shown}
      className={cn(
        "shrink-0 text-lg font-light",
        // Partly right (a multi-answer answer with some points) in the warnings' amber.
        !answer.correct && answer.score
          ? WARNING_TONE
          : gradeTone(answer.correct)
      )}
    >
      {rounds(shown)}
    </span>
  )
}

/** Page leaves and copy attempts while this question was open; nothing when there were none. */
function ScorecardSignals({ item }: { item: ReviewItem }) {
  const t = useTranslations("scorecard")
  const candidates = useTranslations("candidates")
  const signals = [
    item.tab_leaves > 0 && t("leftPage", { count: item.tab_leaves }),
    item.copies > 0 && candidates("copies", { count: item.copies }),
  ].filter(Boolean)

  if (signals.length === 0) {
    return null
  }

  return (
    <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-amber-700 tabular-nums dark:text-amber-400">
      {signals.map((signal, index) => (
        <span key={String(signal)} className="flex items-center gap-x-1.5">
          {index > 0 && <Dot className="mx-0" />}
          {signal}
        </span>
      ))}
    </p>
  )
}

/** "45 s", "2 min 5 s". */
function useDuration() {
  const t = useTranslations("scorecard")

  return (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60

    if (m === 0) {
      return t("seconds", { s })
    }

    return s === 0 ? t("minutes", { m }) : t("minutesSeconds", { m, s })
  }
}

function ScorecardAnswer({
  item,
  language,
}: {
  item: ReviewItem
  language: string
}) {
  const t = useTranslations("scorecard")
  const duration = useDuration()

  if (!item.answer || item.answer.timed_out) {
    return null
  }

  const { seconds, fast, picks } = item.answer

  return (
    <div className="space-y-2">
      {/* A multi-answer question's ticks, each marked right or wrong, with the points. */}
      {item.multi ? (
        <>
          <div {...languageOf(language)}>
            <AnswerOptions
              options={picks.map((index) => ({
                answer: item.options[index],
                correct: Boolean(item.correct_indexes?.includes(index)),
              }))}
              className="rounded-xl bg-surface px-5 py-4 text-lg font-light"
            />
          </div>
          <AnswerPoints item={item} />
        </>
      ) : (
        <p
          {...languageOf(language)}
          className="bidi-auto rounded-xl bg-surface px-5 py-4 text-lg leading-relaxed font-light whitespace-pre-wrap"
        >
          <InlineText text={item.options[picks[0]]} />
        </p>
      )}
      {/* Not known for answers given before timing was recorded. */}
      {seconds != null && (
        <p
          className={cn("text-sm text-muted-foreground", fast && WARNING_TONE)}
        >
          {t.rich("answeredIn", {
            time: duration(seconds),
            b: (chunks) => (
              <span
                className={cn(
                  "tabular-nums",
                  fast ? "font-medium" : "text-foreground"
                )}
              >
                {chunks}
              </span>
            ),
          })}
          {fast && t("tooFast")}
        </p>
      )}
    </div>
  )
}
