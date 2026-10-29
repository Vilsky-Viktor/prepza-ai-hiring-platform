import { cn } from "cn"
import { CornerRightDownIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { type ReactNode, useEffect, useRef, useState } from "react"

import {
  FinishDialog,
  SessionFooter,
} from "@/features/company/components/session-finish"
import { SessionHeader } from "@/features/company/components/session-header"
import { QuestionActions } from "@/components/common/question-actions"
import { MultiChoiceTag } from "@/components/common/multi-choice-tag"
import { QuestionText } from "@/components/common/question-text"
import { CARD_PADDING } from "@/config/cards"
import { ChoiceOptions } from "@/features/company/components/choice-options"
import { useIntegritySignals } from "@/hooks/use-integrity-signals"
import { useScrolls } from "@/hooks/use-scrolls"
import { languageOf } from "@/lib/locale"
import { proseAndCode } from "@/lib/question-text"
import type { InterviewSession } from "@/types/company"
import type { AnswerInput, NextQuestion } from "@/types/round"

type SessionPlayProps = {
  session: InterviewSession
  progress: { answered: number; total: number }
  // This topic's place among the interview's sections.
  section: { number: number; count: number }
  question: NextQuestion | null
  onAnswer: (input: AnswerInput) => Promise<boolean>
  onAdvance: () => Promise<void>
  onFinish: () => Promise<void>
  finishing: boolean
  // A company member's preview: the way back, beside the header.
  back?: ReactNode
  // The company's logo, small, before the section's title.
  brand?: ReactNode
}

export function SessionPlay({
  session,
  progress,
  section,
  question,
  onAnswer,
  onAdvance,
  onFinish,
  finishing,
  back,
  brand,
}: SessionPlayProps) {
  const t = useTranslations("session")
  const locale = useLocale()
  const [confirmFinish, setConfirmFinish] = useState(false)
  // The question whose clock ran out, announced to screen readers; the screen moves on quietly.
  const [timedOut, setTimedOut] = useState<string | null>(null)
  // The options picked on the question on screen (one, or any for a multi-answer question):
  // they can change until they're sent, on Next, on finishing or when the time runs out.
  const [pick, setPick] = useState<{ question: string; options: number[] }>({
    question: "",
    options: [],
  })
  const [sending, setSending] = useState(false)
  useIntegritySignals(session.id, session.status === "in_progress")
  const questionRef = useRef<HTMLDivElement>(null)
  const questionId = question?.question_id
  // A long question scrolls in its own box, which then takes keyboard focus to scroll by keys.
  const { ref: cardRef, scrolls } = useScrolls<HTMLDivElement>(questionId)
  const chosen = pick.question === questionId ? pick.options : []
  const multi = Boolean(question?.multi)
  const { prose, code } = proseAndCode(question?.text ?? "")
  const answered = progress.answered + (chosen.length ? 1 : 0)
  const allAnswered = progress.total > 0 && answered === progress.total

  // Each new question takes focus, so the keyboard and screen readers start from it.
  useEffect(() => {
    if (questionId) {
      questionRef.current?.querySelector<HTMLElement>("[role=heading]")?.focus()
    }
  }, [questionId])

  // Saves the pick, if there is one, then does `then`; when saving fails, only if `always`.
  // Nothing can be picked and the clock can't move on while it's sent, so neither Next nor the
  // clock can move on twice; a failed send keeps the question's real time left.
  async function sendThen(then: () => Promise<void>, always = false) {
    setSending(true)

    try {
      const saved =
        chosen.length === 0 ||
        (await onAnswer(
          multi ? { picks: chosen } : { option_index: chosen[0] }
        ))

      if (saved || always) {
        await then()
      }
    } finally {
      setSending(false)
    }
  }

  const sendAndAdvance = () => sendThen(onAdvance)

  // A multi-answer question's option is ticked or unticked on its own; otherwise it's the pick.
  function choose(questionId: string, option: number) {
    const options = !multi
      ? [option]
      : chosen.includes(option)
        ? chosen.filter((index) => index !== option)
        : [...chosen, option]
    setPick({ question: questionId, options })
  }

  return (
    <div className="space-y-8 pb-28">
      {/* On phones the way back and the logo share a line, the progress under them. */}
      <div className="relative max-sm:flex max-sm:flex-wrap max-sm:items-center max-sm:gap-x-2 max-sm:gap-y-4">
        {back}
        <SessionHeader
          brand={brand}
          session={session}
          progress={progress}
          section={section}
          question={question}
          sending={sending}
          // The pick counts, and quietly on to the next question: a message would only distract.
          onTimeUp={() => {
            setTimedOut(question?.question_id ?? null)
            // The question's time is over even if its pick can't be saved: the next opens.
            void sendThen(onAdvance, true)
          }}
        />
      </div>
      <p aria-live="polite" className="sr-only">
        {timedOut && <span key={timedOut}>{t("timeUp")}</span>}
      </p>
      {question && (
        // The question at the start of the line (on the left, on the right in a right-to-left
        // interface), its options beside it; on phones stacked, the question first. A long
        // question scrolls in its own column, which stays in view while the options scroll.
        <div
          key={question.question_id}
          ref={questionRef}
          className="grid grid-cols-1 gap-6 lg:grid-cols-2 lg:items-start lg:gap-8"
        >
          {/* The question and its rating stay in view together; on phones the
              rating moves under the options. */}
          <div className="contents lg:sticky lg:top-6 lg:block lg:space-y-6">
            {/* Both columns in the interview's own language, so screen readers read them with the
                right voice. Multi-answer questions are tagged just above their text, so they can't
                be taken for single-answer ones. */}
            <div
              {...languageOf(session.language)}
              ref={cardRef}
              data-testid="question-card"
              {...(scrolls && {
                tabIndex: 0,
                role: "region",
                "aria-label": t("question"),
              })}
              className="space-y-3 outline-none focus-visible:ring-3 focus-visible:ring-ring/50 lg:max-h-[calc(100dvh-26rem)] lg:overflow-y-auto"
            >
              {/* The question in its card, its code examples under it. */}
              <div
                data-testid="question-box"
                className={cn(
                  "space-y-3 rounded-xl bg-surface max-sm:-mx-6 max-sm:rounded-none",
                  CARD_PADDING
                )}
              >
                {/* The tag and the hint are the site's, so read in its language. */}
                {multi && (
                  <div {...languageOf(locale)}>
                    <MultiChoiceTag />
                  </div>
                )}
                <QuestionText
                  heading
                  text={prose}
                  className="text-2xl leading-snug font-medium"
                />
              </div>
              {code && <QuestionText text={code} />}
            </div>
            <div
              {...languageOf(locale)}
              data-testid="question-rating"
              className="max-lg:order-last"
            >
              <QuestionActions
                basePath={`/rounds/sessions/${session.id}/questions/${question.question_id}`}
              />
            </div>
          </div>
          <div {...languageOf(session.language)} className="space-y-6">
            {multi && (
              <p
                {...languageOf(locale)}
                data-testid="select-all"
                className="flex items-center gap-1.5 text-sm text-muted-foreground"
              >
                {t("selectAll")}
                {/* Points down to the options. */}
                <CornerRightDownIcon
                  aria-hidden
                  className="size-4 text-primary rtl:-scale-x-100"
                />
              </p>
            )}
            {/* Candidates never learn whether they were right: their picks only stay marked. */}
            <ChoiceOptions
              options={question.options}
              chosen={chosen}
              multi={multi}
              disabled={sending}
              bleed
              onChoose={(option) => choose(question.question_id, option)}
            />
          </div>
        </div>
      )}
      <SessionFooter
        finishing={finishing}
        sending={sending}
        picked={chosen.length > 0}
        onFinish={() => setConfirmFinish(true)}
        onNext={sendAndAdvance}
      />
      <FinishDialog
        open={confirmFinish}
        finishing={finishing}
        sections={section.count}
        unanswered={allAnswered ? null : progress.total - answered}
        onClose={() => setConfirmFinish(false)}
        // The pick on screen is saved first, so it counts; finishing goes ahead even when it
        // can't be saved.
        onFinish={() => sendThen(onFinish, true)}
      />
    </div>
  )
}
