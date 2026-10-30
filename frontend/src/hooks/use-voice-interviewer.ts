"use client"

import { useEffect, useRef, useState } from "react"

import { apiErrorMessage } from "@/lib/api"
import { acknowledgement } from "@/lib/voice-acknowledgement"
import {
  clipUrl,
  playClip,
  prepareNextQuestion,
  sendSpokenAnswer,
} from "@/lib/voice-clips"
import { type Meter, meters, soundAllowed } from "@/lib/voice-meters"
import { type Listener, listen, openMicrophone } from "@/lib/voice-listening"
import { micDetector } from "@/lib/voice-vad"
import { recordingType } from "@/lib/voice"
import type {
  VoiceAnnouncement,
  VoiceAnswer,
  VoiceHandlers,
  VoiceStatus,
} from "@/types/round"

/** Voice mode for the question on screen: Mira, the AI interviewer, reads each question aloud,
 * listens all the time, sends each stretch of speech to be understood, and says what it heard
 * ("You chose B. Is that right?"); a yes sends the choice. Tapping always works too. `chosen`:
 * the options picked on screen. */
export function useVoiceInterviewer(
  sessionId: string,
  questionId: string | undefined,
  chosen: number[],
  handlers: VoiceHandlers
) {
  const [status, setStatus] = useState<VoiceStatus>("off")
  const [heard, setHeard] = useState<string | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const audio = useRef<HTMLAudioElement | null>(null)
  const context = useRef<AudioContext | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const listener = useRef<Listener | null>(null)
  // The levels of what Mira says and what the microphone hears, for the waves.
  const meter = useRef<Meter | null>(null)
  // What the listener's handlers, made once at the start, must read fresh: an interview of several
  // sections moves to each next section's session on the same screen.
  const latest = useRef({
    sessionId,
    chosen,
    handlers,
    questionId,
    status,
  })
  // Mira asked again for this question's answer: she asks once, then just listens.
  const askedAgain = useRef(false)
  // The last answer was confirmed by voice: if the interview ends with it, Mira says goodbye.
  const confirmed = useRef(false)
  const gotIt = useRef(acknowledgement())

  useEffect(() => {
    latest.current = { sessionId, chosen, handlers, questionId, status }
  })

  /** Plays `path`'s clip to its end, then listens (unless `more` follows at once). The microphone
   * is off while Mira speaks: the browser's echo cancelling doesn't cover a page's own audio, so
   * it would hear her from the speakers and take it for the candidate interrupting. */
  async function say(path: string, more = false) {
    const player = audio.current

    if (!player) {
      return
    }

    setStatus("speaking")
    listener.current?.pause()

    try {
      await playClip(player, path)
    } catch (error) {
      // Unread: the question is on screen, and listening goes on.
      console.warn("Mira's clip didn't play", error)
    }

    if (!more) {
      heardAll()
    }
  }

  function heardAll() {
    setStatus("listening")
    hearAgain()
  }

  /** Listening starts afresh. */
  function hearAgain() {
    listener.current?.resume()
  }

  async function understood(answer: VoiceAnswer) {
    // No words (a cough, a knock): ignored, as if nothing was said.
    if (answer.intent === "noise") {
      heardAll()

      return
    }

    setHeard(answer.heard || null)

    if (answer.intent === "confirm") {
      confirmed.current = true

      // Moved on: Mira stays thinking until the next question is read. Not sent: she listens.
      if (!(await latest.current.handlers.onConfirm())) {
        heardAll()
      }

      return
    }

    if (answer.intent === "choose") {
      latest.current.handlers.onPick(
        latest.current.questionId ?? "",
        answer.picks
      )
      const query = answer.picks.map((pick) => `picks=${pick}`).join("&")
      await say(`${latest.current.sessionId}/voice/confirmations?${query}`)

      return
    }

    // Asking for the answer again (a no, or words she didn't catch): once a question.
    if (askedAgain.current) {
      heardAll()

      return
    }

    askedAgain.current = true
    await say(
      `${latest.current.sessionId}/voice/phrases/${answer.intent === "reject" ? "again" : "unclear"}`
    )
  }

  /** Sends the speech and, at once, says "Got it." (not after a cough; still thinking, the
   * microphone paused); what follows the answer waits for it to end. */
  async function onSpeech(recording: Blob, voicedMs: number) {
    const { sessionId: id, chosen: waiting } = latest.current
    setStatus("thinking")
    const sent = sendSpokenAnswer(id, recording, waiting)
    const said =
      audio.current && gotIt.current.play(audio.current, id, voicedMs)

    try {
      const answer = await sent
      await said
      await understood(answer)
    } catch (error) {
      await said
      setProblem(apiErrorMessage(error, latest.current.handlers.failedMessage))
      heardAll()
    }
  }

  function onSpeechStart() {
    setStatus("hearing")
  }

  /** Starts voice mode as the screen opens (the start page's tap allowed sound and the
   * microphone), or on the tap a reloaded page asks for. A start overtaken by another (React's
   * double start in development) gives way. */
  async function start() {
    stop()
    const type = recordingType()
    const ctx = new AudioContext()
    const player = new Audio()
    context.current = ctx
    audio.current = player
    setStatus("starting")

    try {
      const allowed = await soundAllowed(ctx)

      if (context.current !== ctx) {
        return
      }

      if (!allowed) {
        stop()
        setStatus("blocked")

        return
      }

      if (!type) {
        throw new Error("This browser can't record")
      }

      const mic = await openMicrophone()

      if (context.current !== ctx) {
        mic.getTracks().forEach((track) => track.stop())

        return
      }

      stream.current = mic
      meter.current = meters(ctx, player, mic)
      // The speech detector loads while Mira reads the first question.
      const listening = listen(mic, type, micDetector(ctx, mic), {
        onSpeechStart,
        onSpeech: (recording, voicedMs) => void onSpeech(recording, voicedMs),
      })
      listening.catch(() => undefined)
      void gotIt.current.load(sessionId).catch(() => undefined)
      prepareNextQuestion(sessionId)
      await say(`${sessionId}/voice/question`, true)
      const ready = await listening

      // Stopped meanwhile: the detector goes too.
      if (context.current !== ctx) {
        return ready.stop()
      }

      listener.current = ready
      heardAll()
    } catch {
      if (context.current === ctx) {
        stop()
        setStatus("unavailable")
      }
    }
  }

  /** The microphone and the sound off. */
  function stop() {
    listener.current?.stop()
    listener.current = null
    meter.current = null
    stream.current?.getTracks().forEach((track) => track.stop())
    stream.current = null
    void context.current?.close()
    context.current = null
    audio.current?.pause()
    setStatus("off")
  }

  // Each new question is read aloud.
  useEffect(() => {
    if (!questionId || !listener.current) {
      return
    }

    prepareNextQuestion(sessionId)
    askedAgain.current = false
    confirmed.current = false
    setHeard(null)
    setProblem(null)
    void say(`${sessionId}/voice/question`)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionId])

  // The microphone is freed at the interview's end; one ended on a spoken yes gets a goodbye.
  useEffect(
    () => () => {
      if (listener.current && confirmed.current) {
        void clipUrl(`${sessionId}/voice/phrases/end`)
          .then((url) => new Audio(url).play())
          .catch(() => undefined)
      }

      stop()
      gotIt.current.release()
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  return {
    status,
    heard,
    problem,
    meter,
    start,
    // Before the next question is asked for: Mira says she's moving on (an answer was sent, or
    // the time ran out); resolves once she has said it, so the next question's clock, which the
    // server starts as it opens, starts as she reads it.
    announce: (said: VoiceAnnouncement) => {
      // Moving on: the last answer heard is cleared at once.
      setHeard(null)

      return say(`${latest.current.sessionId}/voice/phrases/${said}`, true)
    },
  }
}
