"use client"

import { cn } from "cn"
import { LoaderCircleIcon, MicIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useEffectEvent, useRef, useState } from "react"

import { Count } from "@/components/common/count"
import { Button } from "@/components/ui/button"
import { CANCEL_DISTANCE_PX } from "@/config/assistant"
import { ROUND_ICON_BUTTON } from "@/config/buttons"
import { apiErrorMessage } from "@/lib/api"
import { transcribe } from "@/lib/assistant"
import {
  clock,
  movedAway,
  nextPhase,
  recordingType,
  startRecording,
  type Recording,
  type VoiceEvent,
  type VoicePhase,
} from "@/lib/voice"

/** Push to talk: hold to record, let go to send what was said as a message; sliding away or
 * Esc cancels. From the keyboard, Enter or Space starts and stops. Stops by itself after
 * `maxSeconds`. Not shown where the browser can't record. Its status (recording, transcribing,
 * an error) shows above the input row it sits in. */
export function VoiceButton({
  maxSeconds,
  disabled,
  onTranscript,
}: {
  maxSeconds: number
  disabled?: boolean
  onTranscript: (text: string) => void
}) {
  const t = useTranslations("assistant.voice")
  // The panel renders only in the browser, once opened.
  const [type] = useState(recordingType)
  const [phase, setPhase] = useState<VoicePhase>("idle")
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState<string | null>(null)
  // The phase as async steps read it, between renders.
  const current = useRef<VoicePhase>("idle")
  const recording = useRef<Recording | null>(null)
  // Where a held press started; null when nothing is held.
  const origin = useRef<{ x: number; y: number } | null>(null)
  // Let go before the microphone started (its permission prompt, say).
  const released = useRef(false)

  function step(event: VoiceEvent) {
    current.current = nextPhase(current.current, event)
    setPhase(current.current)
  }

  async function start() {
    if (current.current !== "idle" || !type) {
      return
    }

    setError(null)
    released.current = false

    try {
      const started = await startRecording(type)

      if (released.current) {
        started.cancel()
        setError(t("holdHint"))

        return
      }

      recording.current = started
      setElapsed(0)
      step("start")
    } catch (failure) {
      const name = (failure as Error).name
      setError(
        name === "NotAllowedError"
          ? t("notAllowed")
          : name === "NotFoundError"
            ? t("noMicrophone")
            : t("failed")
      )
    }
  }

  async function stop() {
    if (current.current !== "recording" || !recording.current) {
      return
    }

    step("stop")
    const audio = await recording.current.stop()
    recording.current = null

    if (!audio) {
      step("done")
      setError(t("tooShort"))

      return
    }

    try {
      const text = await transcribe(audio)
      step("done")
      onTranscript(text)
    } catch (failure) {
      step("done")
      setError(apiErrorMessage(failure, t("failed")))
    }
  }

  function cancel() {
    if (current.current !== "recording") {
      return
    }

    recording.current?.cancel()
    recording.current = null
    step("cancel")
  }

  const tick = useEffectEvent((seconds: number) => {
    setElapsed(seconds)

    if (seconds >= maxSeconds) {
      void stop()
    }
  })
  const escape = useEffectEvent(cancel)

  // While recording: the time so far, a stop at the limit, and Esc to cancel.
  useEffect(() => {
    if (phase !== "recording") {
      return
    }

    const started = Date.now()
    const timer = setInterval(() => tick((Date.now() - started) / 1000), 200)

    function onKey(event: KeyboardEvent) {
      // Before the panel hears it: Esc cancels the recording, not the panel.
      if (event.key === "Escape") {
        event.stopPropagation()
        escape()
      }
    }

    window.addEventListener("keydown", onKey, true)

    return () => {
      clearInterval(timer)
      window.removeEventListener("keydown", onKey, true)
    }
  }, [phase])

  // Leaving the panel drops a recording.
  useEffect(() => () => recording.current?.cancel(), [])

  if (!type) {
    return null
  }

  function onPointerDown(event: React.PointerEvent<HTMLButtonElement>) {
    if (event.button !== 0) {
      return
    }

    event.currentTarget.setPointerCapture(event.pointerId)
    origin.current = { x: event.clientX, y: event.clientY }
    void start()
  }

  function onPointerMove(event: React.PointerEvent<HTMLButtonElement>) {
    const to = { x: event.clientX, y: event.clientY }

    if (origin.current && movedAway(origin.current, to, CANCEL_DISTANCE_PX)) {
      origin.current = null
      released.current = true
      cancel()
    }
  }

  function onPointerUp() {
    if (!origin.current) {
      return
    }

    origin.current = null
    released.current = true
    void stop()
  }

  function onPointerCancel() {
    origin.current = null
    released.current = true
    cancel()
  }

  // A click from the keyboard (detail 0) toggles; a pointer's press and release do the rest.
  function onClick(event: React.MouseEvent<HTMLButtonElement>) {
    if (event.detail !== 0) {
      return
    }

    if (current.current === "recording") {
      void stop()
    } else {
      void start()
    }
  }

  const recordingNow = phase === "recording"
  const status = recordingNow
    ? t("recording")
    : phase === "transcribing"
      ? t("transcribing")
      : error

  return (
    <>
      <p
        role="status"
        className={cn(
          "absolute inset-x-0 bottom-[calc(100%+1.25rem)] flex items-center justify-center gap-2 text-center text-sm",
          error && phase === "idle"
            ? "text-destructive"
            : "text-muted-foreground"
        )}
      >
        {recordingNow && (
          <span aria-hidden className="size-2 rounded-full bg-destructive" />
        )}
        {status}
        {recordingNow && (
          <span aria-hidden className="tabular-nums">
            <Count done={clock(elapsed)} total={clock(maxSeconds)} />
          </span>
        )}
      </p>
      <Button
        type="button"
        size="icon"
        variant="ghost"
        className={cn(
          ROUND_ICON_BUTTON,
          "size-10 touch-none select-none",
          recordingNow &&
            "bg-destructive text-white hover:bg-destructive hover:text-white"
        )}
        disabled={disabled || phase === "transcribing"}
        aria-pressed={recordingNow}
        aria-label={recordingNow ? t("stop") : t("hold")}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerCancel}
        onClick={onClick}
        onContextMenu={(event) => event.preventDefault()}
      >
        {phase === "transcribing" ? (
          <LoaderCircleIcon className="size-5 animate-spin" />
        ) : (
          <MicIcon className="size-5" />
        )}
      </Button>
    </>
  )
}
