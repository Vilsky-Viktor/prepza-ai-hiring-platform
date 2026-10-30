"use client"

import { useEffect, useRef, useState } from "react"

import { KEPT_PHRASES, TIME_UP_HOLD_MS } from "@/config/voice"

import { apiErrorMessage } from "@/lib/api"
import { acknowledgement } from "@/lib/voice-acknowledgement"
import { answerInProgress } from "@/lib/voice-answering"
import { react } from "@/lib/voice-reaction"
import { clipUrl, prepareNextQuestion } from "@/lib/voice-clips"
import { keptClips, savedClips } from "@/lib/voice-kept-clips"
import { type Meter, meters, soundAllowed } from "@/lib/voice-meters"
import { type Listener, listen, openMicrophone } from "@/lib/voice-listening"
import { liveListening } from "@/lib/voice-live"
import { turnTiming } from "@/lib/voice-timing"
import { micDetector } from "@/lib/voice-vad"
import { recordingType } from "@/lib/voice"
import type {
  VoiceAnnouncement,
  VoiceAnswer,
  VoiceHandlers,
  VoiceStatus,
} from "@/types/round"

/** Voice mode for the question on screen: Mira, the AI interviewer, reads each question aloud,
 * listens all the time, sends each stretch of speech to be understood, and says what it heard: a
 * clear answer is sent at once ("B, saved."), any other is confirmed first ("You chose B. Is
 * that right?"), a yes sending it. Tapping always works too. `chosen`:
 * the options picked on screen; `letters`: how many options' "{letter}, saved." Mira may say
 * (none on a multi-answer question), fetched ahead. */
export function useVoiceInterviewer(
  sessionId: string,
  questionId: string | undefined,
  chosen: number[],
  letters: number,
  handlers: VoiceHandlers
) {
  const [status, setStatus] = useState<VoiceStatus>("off")
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
  // The last answer was saved by voice (confirmed, or clear): if the interview ends with it, Mira
  // says goodbye.
  const confirmed = useRef(false)
  // Her short clips, kept in the page.
  const clips = useRef(keptClips())
  const gotIt = useRef(acknowledgement(clips.current))
  // How long each answer's turn took, for Sentry.
  const timing = useRef(turnTiming())
  // The answer being heard or understood, the question's own.
  const inProgress = useRef(answerInProgress())
  // Listening live: the speech streamed as it's said, and the answer it gives once it ends.
  const live = useRef(liveListening(latest))

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
    gotIt.current.cancel(player)
    // The first clip after an answer is her reaction to it.
    player.onplaying = () => timing.current.reacted()

    try {
      await clips.current.play(player, path)
    } catch (error) {
      // Unread: the question is on screen, and listening goes on.
      console.warn("Mira's clip didn't play", error)
    } finally {
      player.onplaying = null
    }

    if (!more) {
      heardAll()
    }
  }

  /** Listening starts afresh; an answer Mira said nothing to isn't timed. */
  function heardAll() {
    timing.current.dropped()
    setStatus("listening")
    listener.current?.resume()
  }

  function understood(answer: VoiceAnswer) {
    const { sessionId: id, questionId: question, handlers } = latest.current

    return react(answer, {
      sessionId: id,
      questionId: question ?? "",
      handlers,
      confirmed,
      say: (path) => say(path),
      listen: heardAll,
    })
  }

  /** The speech ended: its answer as heard live, or else the recording sent whole (still
   * thinking, the microphone paused); "Got it." fills the wait only when the answer is slow, and
   * stops the moment it's back. */
  async function onSpeech(recording: Blob, voicedMs: number) {
    const id = latest.current.sessionId
    setStatus("thinking")
    timing.current.ended()
    const sent = live.current.answer(recording)

    if (audio.current) {
      gotIt.current.schedule(audio.current, id, voicedMs)
    }

    // After the time ran out, the screen alone acts on the answer (timeUp).
    try {
      const { answer, stages, live: streamed } = await sent
      gotIt.current.cancel(audio.current)
      timing.current.answered(answer, stages, streamed)
      inProgress.current.end(answer)

      await (inProgress.current.timedOut()
        ? timing.current.dropped()
        : understood(answer))
    } catch (error) {
      gotIt.current.cancel(audio.current)
      timing.current.dropped()
      inProgress.current.end(null)
      setProblem(apiErrorMessage(error, latest.current.handlers.failedMessage))
      await (inProgress.current.timedOut() || heardAll())
    }
  }

  function onSpeechStart() {
    inProgress.current.begin()
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
      const listening = listen(
        mic,
        type,
        micDetector(ctx, mic),
        {
          onSpeechStart,
          onSpeech: (recording, voicedMs) => void onSpeech(recording, voicedMs),
        },
        live.current
      )
      listening.catch(() => undefined)
      clips.current.preload(sessionId, [
        ...KEPT_PHRASES,
        ...savedClips(letters),
      ])
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
    clips.current.preload(sessionId, savedClips(letters))
    inProgress.current = answerInProgress()
    confirmed.current = false
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
      clips.current.release()
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  return {
    status,
    problem,
    meter,
    start,
    // Before the next question is asked for: Mira says she's moving on (an answer was sent, or
    // the time ran out); resolves once she has said it, so the next question's clock, which the
    // server starts as it opens, starts as she reads it.
    announce: (said: VoiceAnnouncement) =>
      say(`${latest.current.sessionId}/voice/phrases/${said}`, true),
    // A clear answer was saved: Mira says so ("B, saved."), resolving once she has, as announce.
    announceSaved: (pick: number) =>
      say(`${latest.current.sessionId}/voice/saved/${pick}`, true),
    // The question's time ran out: speech begun in time is sent and waited for; the options it
    // picked (saved without a confirmation), or null.
    timeUp: () => {
      listener.current?.flush()

      return inProgress.current.timeUp(TIME_UP_HOLD_MS)
    },
  }
}
