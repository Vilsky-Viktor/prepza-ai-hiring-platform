import type { VoiceAnswer } from "@/types/round"

/** The spoken answer in progress, from the moment the candidate is heard speaking until the
 * service has understood it. When the question's time runs out meanwhile, the screen waits for
 * it: speech begun in time counts (the service accepts it a little past the deadline, rounds'
 * services/voice_deadline.py). */
export function answerInProgress() {
  let pending: {
    answer: Promise<VoiceAnswer | null>
    done: (answer: VoiceAnswer | null) => void
  } | null = null
  let timedOut = false

  return {
    begin: () => {
      if (pending) {
        return
      }

      let done: (answer: VoiceAnswer | null) => void = () => undefined
      const answer = new Promise<VoiceAnswer | null>((resolve) => {
        done = resolve
      })
      pending = { answer, done }
    },
    // Understood (null: it failed, or was dropped).
    end: (answer: VoiceAnswer | null) => {
      pending?.done(answer)
      pending = null
    },
    // Whether the question's time ran out: the screen alone acts on the answer then.
    timedOut: () => timedOut,
    /** The question's time ran out: the options the answer picked (a choice, or the yes to the
     * choice waiting), waited for at most `ms`; null when nothing is in progress, it picked
     * nothing, or it took longer. */
    timeUp: async (ms: number) => {
      timedOut = true

      if (!pending) {
        return null
      }

      const answer = await Promise.race([
        pending.answer,
        new Promise<null>((done) => window.setTimeout(() => done(null), ms)),
      ])
      const picked = answer?.intent === "choose" || answer?.intent === "confirm"

      return picked ? answer.picks : null
    },
  }
}
