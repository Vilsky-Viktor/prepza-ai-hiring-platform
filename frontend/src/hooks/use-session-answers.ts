"use client"

import { useEffect, useRef, useState } from "react"

import type { AnswerInput } from "@/types/round"

/** The options picked on the question on screen and how they're sent, shared by the interview's
 * click and voice screens. Picks (one, or any for a multi-answer question) can change until
 * they're sent, on Next, on finishing or when the time runs out. */
export function useSessionAnswers(
  questionId: string | undefined,
  multi: boolean,
  progress: { answered: number; total: number },
  onAnswer: (input: AnswerInput) => Promise<boolean>
) {
  const [pick, setPick] = useState<{ question: string; options: number[] }>({
    question: "",
    options: [],
  })
  const [sending, setSending] = useState(false)
  const chosen = pick.question === questionId ? pick.options : []
  const answered = progress.answered + (chosen.length ? 1 : 0)
  const allAnswered = progress.total > 0 && answered === progress.total

  // Saves the pick (`picks`, or the one on screen) and does `then` as `sendPicks` does.
  // Nothing can be picked and the clock can't move on while it's sent, so neither Next nor the
  // clock can move on twice; a failed send keeps the question's real time left.
  async function sendThen(
    then: (saved: boolean) => Promise<void>,
    always = false,
    picks = chosen
  ) {
    setSending(true)

    try {
      return await sendPicks(picks, multi, onAnswer, then, always)
    } finally {
      setSending(false)
    }
  }

  function choose(question: string, option: number) {
    setPick({ question, options: toggled(chosen, option, multi) })
  }

  return {
    chosen,
    sending,
    answered,
    allAnswered,
    sendThen,
    choose,
    setPick,
  }
}

/** Saves `picks`, if there are any, then does `then`, told whether a pick was saved; when saving
 * fails, only if `always`. Whether `then` was done. */
export async function sendPicks(
  picks: number[],
  multi: boolean,
  onAnswer: (input: AnswerInput) => Promise<boolean>,
  then: (saved: boolean) => Promise<void>,
  always: boolean
) {
  const saved =
    picks.length === 0 ||
    (await onAnswer(multi ? { picks } : { option_index: picks[0] }))

  if (saved || always) {
    await then(saved && picks.length > 0)

    return true
  }

  return false
}

/** The options picked after a tap on `option`: a multi-answer question's option is ticked or
 * unticked on its own; otherwise it's the pick. */
export function toggled(chosen: number[], option: number, multi: boolean) {
  if (!multi) {
    return [option]
  }

  return chosen.includes(option)
    ? chosen.filter((index) => index !== option)
    : [...chosen, option]
}

/** Each new question takes focus, so the keyboard and screen readers start from it: the ref goes
 * on the element holding its heading. */
export function useQuestionFocus(questionId: string | undefined) {
  const questionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (questionId) {
      questionRef.current?.querySelector<HTMLElement>("[role=heading]")?.focus()
    }
  }, [questionId])

  return questionRef
}
