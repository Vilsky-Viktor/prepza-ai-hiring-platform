import { MIN_RECORDING_MS, RECORDING_TYPES } from "@/constants/assistant"

// The voice button's steps: idle, recording while held, then transcribing what was recorded.
export type VoicePhase = "idle" | "recording" | "transcribing"
export type VoiceEvent = "start" | "stop" | "cancel" | "done"

/** The voice button's next step: a press starts recording, letting go (or the time limit)
 * stops it and transcribes, cancelling drops it; the transcript (or its error) ends it. Any other
 * event changes nothing, so a late or repeated one is harmless. */
export function nextPhase(phase: VoicePhase, event: VoiceEvent): VoicePhase {
  if (phase === "idle" && event === "start") {
    return "recording"
  }

  if (phase === "recording" && event === "stop") {
    return "transcribing"
  }

  if (phase === "recording" && event === "cancel") {
    return "idle"
  }

  if (phase === "transcribing" && event === "done") {
    return "idle"
  }

  return phase
}

/** The first format this browser records in, or null when it can't record at all. */
export function recordingType(): string | null {
  if (
    typeof MediaRecorder === "undefined" ||
    typeof navigator === "undefined" ||
    !navigator.mediaDevices?.getUserMedia
  ) {
    return null
  }

  return (
    RECORDING_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) ?? null
  )
}

/** Whether a pointer moved `limit` px or more away from where the press started. */
export function movedAway(
  from: { x: number; y: number },
  to: { x: number; y: number },
  limit: number
) {
  return Math.hypot(to.x - from.x, to.y - from.y) >= limit
}

/** "0:07": seconds as the recording's elapsed time and its limit show. */
export function clock(seconds: number) {
  const whole = Math.floor(seconds)

  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`
}

export type Recording = {
  // The recording, or null when it was shorter than MIN_RECORDING_MS.
  stop: () => Promise<Blob | null>
  cancel: () => void
}

/** Starts recording the microphone (asking for it the first time). Stopping or cancelling
 * releases it; the audio stays in memory. Throws the browser's error when the microphone isn't
 * allowed ("NotAllowedError") or there is none ("NotFoundError"). */
export async function startRecording(type: string): Promise<Recording> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const recorder = new MediaRecorder(stream, { mimeType: type })
  const chunks: Blob[] = []
  const started = Date.now()

  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      chunks.push(event.data)
    }
  }

  recorder.start()

  function finish(keep: boolean) {
    return new Promise<Blob | null>((resolve) => {
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        const long = Date.now() - started >= MIN_RECORDING_MS
        // The service reads the format without its codec.
        const format = (recorder.mimeType || type).split(";")[0]

        resolve(keep && long ? new Blob(chunks, { type: format }) : null)
      }

      if (recorder.state === "inactive") {
        recorder.onstop?.(new Event("stop"))

        return
      }

      recorder.stop()
    })
  }

  return { stop: () => finish(true), cancel: () => void finish(false) }
}
