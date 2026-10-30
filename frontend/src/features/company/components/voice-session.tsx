import { cn } from "cn"
import { useLocale, useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { MultiChoiceTag } from "@/components/common/multi-choice-tag"
import { QuestionText } from "@/components/common/question-text"
import { QuestionCode } from "@/features/company/components/question-code"
import { RoundFooter } from "@/components/common/round-footer"
import { Button } from "@/components/ui/button"
import { CARD_PADDING } from "@/config/cards"
import { ChoiceOptions } from "@/features/company/components/choice-options"
import { MiraWave } from "@/features/company/components/mira-wave"
import { FinishDialog } from "@/features/company/components/session-finish"
import { SessionTop } from "@/features/company/components/session-header"
import type { SessionPlayProps } from "@/features/company/components/session-play"
import { VoiceHeard } from "@/features/company/components/voice-heard"
import { VoiceTurn } from "@/features/company/components/voice-turn"
import { useIntegritySignals } from "@/hooks/use-integrity-signals"
import {
  useQuestionFocus,
  useSessionAnswers,
} from "@/hooks/use-session-answers"
import { useVoiceInterviewer } from "@/hooks/use-voice-interviewer"
import { useVoiceWaves } from "@/hooks/use-voice-waves"
import { languageOf } from "@/lib/locale"
import { proseAndCode } from "@/lib/question-text"

/** A voice interview's screen: the session's header on top; on one side Mira (the AI
 * interviewer) with the wave her voice moves and her status, then the candidate's own wave and the
 * answer she heard; on the other the question she reads and its options as the same cards as in click mode; at the
 * bottom only End (and Next once an option is tapped, for anyone answering without their
 * voice). She starts speaking as it
 * opens: the start page allowed the microphone and sound. */
export function VoiceSession({
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
  const rounds = useTranslations("rounds")
  const locale = useLocale()
  const [confirmFinish, setConfirmFinish] = useState(false)
  // The question whose clock ran out, announced to screen readers; the screen moves on quietly.
  const [timedOut, setTimedOut] = useState<string | null>(null)
  useIntegritySignals(session.id, session.status === "in_progress")
  const questionId = question?.question_id
  const multi = Boolean(question?.multi)
  const { chosen, sending, answered, allAnswered, sendThen, choose, setPick } =
    useSessionAnswers(questionId, multi, progress, onAnswer)
  const questionRef = useQuestionFocus(questionId)
  const { prose, code } = proseAndCode(question?.text ?? "")
  // Mira says she's moving on before the next question is read.
  const sendAndAdvance = () => {
    voice.announce("next")

    return sendThen(onAdvance)
  }
  // Spoken answers pick options as taps do, and a spoken yes sends them as Next does.
  const voice = useVoiceInterviewer(session.id, questionId, chosen, {
    onPick: (question, options) => setPick({ question, options }),
    onConfirm: sendAndAdvance,
    failedMessage: t("voiceFailed"),
  })
  // The candidate's wave stays flat while Mira speaks: the microphone hears her from the speakers
  // too, and it isn't listening then.
  const waves = useVoiceWaves(voice.meter, voice.status === "speaking")

  // Mira starts as the screen opens.
  useEffect(() => {
    void voice.start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-8 pb-28">
      <SessionTop
        back={back}
        timedOut={timedOut}
        brand={brand}
        session={session}
        progress={progress}
        section={section}
        question={question}
        sending={sending}
        // The pick counts, and quietly on to the next question: a message would only distract.
        onTimeUp={() => {
          setTimedOut(question?.question_id ?? null)
          // The question's time is over even if its pick can't be saved: the next opens. An
          // answer spoken in time is waited for, and what it picked is saved without asking.
          voice.announce("time-up")
          void voice
            .timeUp()
            .then((picks) => sendThen(onAdvance, true, picks ?? undefined))
        }}
      />
      {/* Two parts, 30% and 70%, stacked on phones: the voices (Mira's, then the candidate's with
          the answer heard, a fading line between with whose turn it is) on the start side, the
          question and its options on the other. */}
      <div className="grid grid-cols-1 gap-10 max-sm:gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,7fr)] lg:items-start lg:gap-12">
        <section
          // On phones Mira and the candidate side by side, whose turn under them, so the
          // question shows sooner.
          aria-label={t("voiceInterviewer")}
          data-testid="voice-interviewer"
          data-status={voice.status}
          className="flex flex-col items-center gap-12 text-center max-sm:grid max-sm:grid-cols-2 max-sm:items-start max-sm:gap-x-4 max-sm:gap-y-2 lg:sticky lg:top-6 [&>*]:w-full max-sm:[&>[data-testid=voice-turn]]:order-last max-sm:[&>[data-testid=voice-turn]]:col-span-2"
        >
          <MiraWave
            waveRef={waves.mira}
            status={voice.status}
            picked={chosen.length > 0}
            onSoundOn={() => void voice.start()}
          />
          <VoiceTurn status={voice.status} />
          <VoiceHeard
            waveRef={waves.you}
            problem={voice.problem}
            status={voice.status}
          />
        </section>
        {question && (
          // The question and the options in the interview's own language, so screen readers read
          // them with the right voice; the tag is the site's.
          <div
            key={question.question_id}
            ref={questionRef}
            {...languageOf(session.language)}
            className="flex w-full flex-col gap-6"
          >
            {/* The question in its grey card, as in click mode; its code examples under it. */}
            <div
              data-testid="question-box"
              className={cn(
                "space-y-3 rounded-xl bg-surface max-sm:-mx-6 max-sm:rounded-none",
                CARD_PADDING
              )}
            >
              {multi && (
                <div {...languageOf(locale)}>
                  <MultiChoiceTag />
                </div>
              )}
              <QuestionText
                heading
                text={prose}
                className="text-2xl leading-snug font-normal max-sm:text-xl"
              />
            </div>
            {code && <QuestionCode code={code} />}
            {/* The same option cards as in click mode. */}
            <ChoiceOptions
              options={question.options}
              chosen={chosen}
              multi={multi}
              disabled={sending}
              bleed
              onChoose={(option) => choose(question.question_id, option)}
            />
          </div>
        )}
      </div>
      <RoundFooter>
        <Button
          variant="ghost"
          className="h-12 px-6 text-base"
          disabled={finishing || sending}
          onClick={() => setConfirmFinish(true)}
          data-testid="finish-interview"
        >
          {finishing ? rounds("finishing") : t("voiceEnd")}
        </Button>
        <div className="flex items-center gap-3">
          {chosen.length > 0 && (
            <Button
              className="h-12 px-6 text-base"
              disabled={sending}
              onClick={sendAndAdvance}
              data-testid="next-question"
            >
              {rounds("next")}
            </Button>
          )}
        </div>
      </RoundFooter>
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
