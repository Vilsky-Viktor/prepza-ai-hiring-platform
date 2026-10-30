import { afterEach, beforeEach, expect, it, vi } from "vitest"

import { FRAME_MS, MIN_VOICED_MS, PRE_ROLL_MS } from "@/config/voice"
import type { LiveSink } from "@/lib/voice-listening"

import { LOUD, startListening, stubRecorder } from "./voice-listener"

const PRE_ROLL_FRAMES = Math.ceil(PRE_ROLL_MS / FRAME_MS)

// A live sink that keeps what it's told, in order; the frames by their level, so a test can
// tell the moment before the speech (quiet) from the speech (loud).
function sink() {
  const calls: string[] = []
  let preRoll: number[] = []
  const streamed: number[] = []
  const live: LiveSink = {
    open: () => calls.push("open"),
    start: (frames) => {
      calls.push("start")
      preRoll = frames.map((frame) => frame[0])
    },
    frame: (samples) => streamed.push(samples[0]),
    end: () => calls.push("end"),
    close: () => calls.push("close"),
  }

  return { live, calls, preRoll: () => preRoll, streamed }
}

beforeEach(() => {
  stubRecorder()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

it("prepares a connection as listening starts and streams speech once heard, with the moment before it", async () => {
  const { live, calls, preRoll, streamed } = sink()
  const { listener, events, frames, heard } = await startListening(live)
  listener.resume()

  expect(calls).toEqual(["open"])

  // A second of quiet room, then speech: only its last PRE_ROLL_MS goes before the speech.
  frames(1000, 0.05, 0.001)
  events.onSpeechStart()
  frames(MIN_VOICED_MS, 0.9, LOUD)

  expect(calls).toEqual(["open", "start"])
  expect(preRoll()).toEqual([
    ...Array(PRE_ROLL_FRAMES).fill(Math.fround(0.001)),
    ...Array(MIN_VOICED_MS / FRAME_MS).fill(Math.fround(LOUD)),
  ])

  frames(10 * FRAME_MS, 0.9, LOUD)
  events.onSpeechEnd()

  // The rest as it comes; the end goes before the recording is handed over.
  expect(streamed).toHaveLength(10)
  expect(calls).toEqual(["open", "start", "end"])
  expect(heard).toHaveLength(1)
})

it("never streams a sound that isn't the candidate speaking", async () => {
  const { live, calls, streamed } = sink()
  const { listener, stretch } = await startListening(live)
  listener.resume()
  stretch(2000, 0.3, LOUD)
  stretch(MIN_VOICED_MS - FRAME_MS, 0.9, LOUD)

  expect(calls).toEqual(["open"])
  expect(streamed).toEqual([])
})

it("closes the connection when listening pauses or stops without an answer", async () => {
  const { live, calls } = sink()
  const { listener, events, frames } = await startListening(live)
  listener.resume()
  events.onSpeechStart()
  frames(MIN_VOICED_MS, 0.9, LOUD)
  listener.pause()
  listener.resume()
  listener.stop()

  expect(calls).toEqual(["open", "start", "close", "open", "close"])
})

it("ends speech already heard at once when the time runs out", async () => {
  const { live, calls } = sink()
  const { listener, events, frames, heard } = await startListening(live)
  listener.resume()
  events.onSpeechStart()
  frames(MIN_VOICED_MS, 0.9, LOUD)
  listener.flush()

  expect(calls).toEqual(["open", "start", "end"])
  expect(heard).toHaveLength(1)
})
