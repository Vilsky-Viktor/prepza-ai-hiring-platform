import * as Sentry from "@sentry/nextjs"

import type { VoiceAnswer } from "@/types/round"

const MS = { unit: "millisecond" } as const

/** The service's stages from a Server-Timing header ("transcribe;dur=812, match;dur=3"), in
 * milliseconds. */
export function serverStages(header: string | null) {
  const stages: Record<string, number> = {}

  for (const entry of (header ?? "").split(",")) {
    const [name, ...params] = entry.trim().split(";")
    const duration = params.find((param) => param.trim().startsWith("dur="))

    if (name && duration) {
      stages[name] = Number(duration.trim().slice(4))
    }
  }

  return stages
}

/** One spoken answer's turn, timed from the moment the browser took its speech as ended: when
 * the service's understanding came back (with the service's own stages) and when Mira's
 * reaction started playing. Sent to Sentry as distributions, by what the answer meant and
 * whether it was heard live (lib/voice-live.ts) or sent as a recording: durations only, never
 * the words. "Got it." isn't a reaction: it only fills the wait. */
export function turnTiming() {
  let turn: {
    ended: number
    attributes?: { intent: string; clear: boolean; live: boolean }
  } | null = null

  return {
    ended: () => {
      turn = { ended: performance.now() }
    },
    answered: (
      answer: VoiceAnswer,
      stages: Record<string, number>,
      live: boolean
    ) => {
      if (!turn) {
        return
      }

      const attributes = { intent: answer.intent, clear: answer.clear, live }
      turn.attributes = attributes
      Sentry.metrics.distribution(
        "voice.answer.response",
        performance.now() - turn.ended,
        { ...MS, attributes }
      )

      for (const [stage, ms] of Object.entries(stages)) {
        Sentry.metrics.distribution(`voice.answer.${stage}`, ms, {
          ...MS,
          attributes,
        })
      }
    },
    // Mira's reaction to the answer started playing.
    reacted: () => {
      if (turn?.attributes) {
        Sentry.metrics.distribution(
          "voice.answer.reaction",
          performance.now() - turn.ended,
          { ...MS, attributes: turn.attributes }
        )
      }

      turn = null
    },
    // No reaction follows (noise, a failure, the time ran out).
    dropped: () => {
      turn = null
    },
  }
}
