import { MessageCircleQuestionIcon, TriangleAlertIcon } from "lucide-react"
import { getFormatter, getTranslations } from "next-intl/server"

import { CornerSign } from "@/components/common/corner-sign"
import { QuestionText } from "@/components/common/question-text"
import { SIGN_CARD } from "@/config/cards"
import { languageOf } from "@/lib/locale"
import type { AnswerPatterns } from "@/types/company"

/** Each answer-pattern signal that fired, as its sentence; the numbers come from the API. */
export async function AnswerSignalLines({
  signals,
  className,
}: {
  signals: AnswerPatterns["signals"]
  className?: string
}) {
  const t = await getTranslations("answerPatterns")

  return (
    <ul className={className}>
      {signals.map((signal) =>
        signal.kind === "timing" ? (
          <li key={signal.kind} data-signal={signal.kind}>
            {t("timing")}
          </li>
        ) : (
          <li key={signal.kind} data-signal={signal.kind}>
            {t("personFit", {
              hardRight: signal.hard_right ?? 0,
              hard: signal.hard ?? 0,
              easyWrong: signal.easy_wrong ?? 0,
              easy: signal.easy ?? 0,
            })}
          </li>
        )
      )}
    </ul>
  )
}

/** What a finished candidate's answers and times show, on a card like the invite link's: each
 * signal that fired (an amber sign), then questions they got right to ask about in a live
 * interview, in the interview's `language`. With no signal it's only those questions (the
 * primary sign); nothing before they finish. */
export async function AnswerPatternsCard({
  patterns,
  language,
}: {
  patterns: AnswerPatterns
  language: string
}) {
  const t = await getTranslations("answerPatterns")
  const signalled = patterns.signals.length > 0

  if (!signalled && patterns.follow_ups.length === 0) {
    return null
  }

  return (
    <section
      data-testid="answer-patterns"
      className={`${SIGN_CARD} space-y-5 max-sm:-mx-6 max-sm:rounded-none`}
    >
      <CornerSign>
        {signalled ? (
          <TriangleAlertIcon className="text-amber-600 dark:text-amber-400" />
        ) : (
          <MessageCircleQuestionIcon className="text-primary" />
        )}
      </CornerSign>
      {signalled && (
        <div className="space-y-2 text-base">
          <h2 className="font-medium">{t("title")}</h2>
          <AnswerSignalLines signals={patterns.signals} className="space-y-1" />
          <p className="text-sm text-muted-foreground">{t("note")}</p>
        </div>
      )}
      {patterns.follow_ups.length > 0 && (
        <div className="space-y-3">
          {signalled ? (
            <h3 className="text-sm font-medium">{t("askTitle")}</h3>
          ) : (
            <div className="space-y-1 text-base">
              <h2 className="font-medium lowercase">{t("askTitle")}</h2>
              <p className="text-sm text-muted-foreground">{t("askIntro")}</p>
            </div>
          )}
          <FollowUps followUps={patterns.follow_ups} language={language} />
        </div>
      )}
    </section>
  )
}

/** Each follow-up: its topic, the question, and what to ask about it. */
async function FollowUps({
  followUps,
  language,
}: {
  followUps: AnswerPatterns["follow_ups"]
  language: string
}) {
  const t = await getTranslations("answerPatterns")
  const format = await getFormatter()

  return (
    <ol className="space-y-4">
      {followUps.map((followUp) => (
        <li
          key={followUp.question_id}
          data-testid="follow-up"
          className="space-y-1.5"
        >
          <p
            className="text-sm text-muted-foreground"
            {...languageOf(language)}
          >
            {followUp.topic_title}
          </p>
          <div {...languageOf(language)}>
            <QuestionText text={followUp.text} className="font-light" />
          </div>
          <p className="text-sm">
            {t.rich("ask", {
              answer: format.list(followUp.right),
              other: followUp.wrong,
              b: (chunks) => (
                <bdi className="font-medium" {...languageOf(language)}>
                  {chunks}
                </bdi>
              ),
            })}
          </p>
        </li>
      ))}
    </ol>
  )
}
