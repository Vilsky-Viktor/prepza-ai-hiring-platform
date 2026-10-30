// The listener (lib/voice-listening.ts) driven by hand for its tests: a fake MediaRecorder and a
// detector whose events the test sends.
import { vi } from "vitest"

import { FRAME_MS, SPEECH_LEVEL } from "@/config/voice"
import {
  type DetectorEvents,
  type LiveSink,
  listen,
} from "@/lib/voice-listening"

export const LOUD = SPEECH_LEVEL * 3
export const QUIET = SPEECH_LEVEL / 3

// The recorders made since the last stubRecorder(), the latest last.
export const recorders: FakeRecorder[] = []

class FakeRecorder {
  state = "inactive"
  ondataavailable: ((event: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null

  constructor() {
    recorders.push(this)
  }

  start() {
    this.state = "recording"
  }

  stop() {
    this.state = "inactive"
    this.ondataavailable?.({ data: new Blob(["sound"]) })
    this.onstop?.()
  }
}

/** MediaRecorder as the fake, with no recorders made yet. */
export function stubRecorder() {
  recorders.length = 0
  vi.stubGlobal("MediaRecorder", FakeRecorder)
}

/** A listener on a detector the test drives, with `live` as its live sink when given. */
export async function startListening(live?: LiveSink) {
  const heard: { audio: Blob; voicedMs: number }[] = []
  const onSpeechStart = vi.fn()
  const detector = {
    start: vi.fn(async () => undefined),
    pause: vi.fn(async () => undefined),
    destroy: vi.fn(async () => undefined),
  }
  let events = {} as DetectorEvents
  const listener = await listen(
    {} as MediaStream,
    "audio/webm;codecs=opus",
    async (given) => {
      events = given

      return detector
    },
    {
      onSpeechStart,
      onSpeech: (audio, voicedMs) => heard.push({ audio, voicedMs }),
    },
    live
  )

  // `ms` of frames, each with the detector's probability and the sound's level.
  function frames(ms: number, speech: number, loudness: number) {
    for (let at = 0; at < ms; at += FRAME_MS) {
      events.onFrame(speech, new Float32Array(512).fill(loudness))
    }
  }

  // A stretch the detector takes for speech, from its start to its end.
  function stretch(ms: number, speech: number, loudness: number) {
    events.onSpeechStart()
    frames(ms, speech, loudness)
    events.onSpeechEnd()
  }

  return { listener, detector, events, heard, onSpeechStart, frames, stretch }
}
