import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  FRAME_MS,
  IDLE_RESTART_MS,
  MAX_ANSWER_MS,
  MIN_VOICED_MS,
} from "@/config/voice"
import { level } from "@/lib/voice-listening"

import {
  LOUD,
  QUIET,
  recorders,
  startListening as start,
  stubRecorder,
} from "./voice-listener"

describe("level", () => {
  it("is the sound's root mean square", () => {
    expect(level(new Float32Array([0.5, -0.5, 0.5, -0.5]))).toBeCloseTo(0.5)
    expect(level(new Float32Array(8))).toBe(0)
  })
})

describe("listen", () => {
  beforeEach(() => {
    stubRecorder()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("starts paused and sends a stretch of speech once it ends, with how long it was voiced", async () => {
    const { listener, detector, heard, onSpeechStart, stretch } = await start()
    stretch(1000, 0.9, LOUD)

    expect(heard).toEqual([])
    expect(detector.start).not.toHaveBeenCalled()

    listener.resume()
    stretch(30 * FRAME_MS, 0.9, LOUD)

    expect(detector.start).toHaveBeenCalledOnce()
    expect(onSpeechStart).toHaveBeenCalledOnce()
    expect(heard).toHaveLength(1)
    expect(heard[0].audio.type).toBe("audio/webm")
    expect(heard[0].voicedMs).toBe(30 * FRAME_MS)
    // One answer at a time: the detector waits for the next resume.
    expect(detector.pause).toHaveBeenCalledOnce()
  })

  it("takes a short answer, like a single letter", async () => {
    const { listener, heard, stretch } = await start()
    listener.resume()
    stretch(MIN_VOICED_MS + FRAME_MS, 0.9, LOUD)

    expect(heard).toHaveLength(1)
  })

  it.each([
    ["too short to be words", MIN_VOICED_MS - FRAME_MS, 0.9, LOUD],
    ["not speech (a cough, thunder)", 2000, 0.3, LOUD],
    ["speech too quiet to be the candidate's (a television)", 2000, 0.9, QUIET],
  ])(
    "drops a stretch %s and records afresh",
    async (_, ms, speech, loudness) => {
      const { listener, heard, onSpeechStart, stretch } = await start()
      listener.resume()
      stretch(ms, speech, loudness)

      expect(onSpeechStart).not.toHaveBeenCalled()
      expect(heard).toEqual([])
      expect(recorders.at(-1)?.state).toBe("recording")
      expect(recorders).toHaveLength(2)
    }
  )

  it("drops a stretch the detector gave up on", async () => {
    const { listener, events, heard, frames } = await start()
    listener.resume()
    events.onSpeechStart()
    frames(FRAME_MS, 0.9, LOUD)
    events.onMisfire()

    expect(heard).toEqual([])
    expect(recorders).toHaveLength(2)
  })

  it("never sends silence, recording afresh while nobody speaks", async () => {
    const { listener, heard, frames } = await start()
    listener.resume()
    frames(IDLE_RESTART_MS * 3, 0.05, 0)

    expect(heard).toEqual([])
    expect(recorders.length).toBeGreaterThan(2)
  })

  it("sends an answer that reaches the longest an answer may be", async () => {
    const { listener, events, heard, frames } = await start()
    listener.resume()
    events.onSpeechStart()
    frames(MAX_ANSWER_MS, 0.9, LOUD)

    expect(heard).toHaveLength(1)
  })

  it("hears nothing while paused and starts afresh on resume", async () => {
    const { listener, detector, heard, stretch } = await start()
    listener.resume()
    listener.pause()
    stretch(1000, 0.9, LOUD)

    expect(heard).toEqual([])
    expect(detector.pause).toHaveBeenCalledOnce()

    listener.resume()
    stretch(1000, 0.9, LOUD)

    expect(heard).toHaveLength(1)
  })

  it("waits for a resume after sending, so one answer is sent at a time", async () => {
    const { listener, heard, stretch } = await start()
    listener.resume()
    stretch(1000, 0.9, LOUD)
    stretch(1000, 0.9, LOUD)

    expect(heard).toHaveLength(1)
  })

  it("sends speech already heard at once when the time runs out, and drops anything else", async () => {
    const heardOnTime = await start()
    heardOnTime.listener.resume()
    heardOnTime.events.onSpeechStart()
    heardOnTime.frames(MIN_VOICED_MS, 0.9, LOUD)
    heardOnTime.listener.flush()

    expect(heardOnTime.heard).toHaveLength(1)
    expect(heardOnTime.detector.pause).toHaveBeenCalledOnce()

    const notYet = await start()
    notYet.listener.resume()
    notYet.events.onSpeechStart()
    notYet.frames(FRAME_MS, 0.9, LOUD)
    notYet.listener.flush()
    notYet.frames(1000, 0.9, LOUD)
    notYet.events.onSpeechEnd()

    expect(notYet.heard).toEqual([])
    expect(notYet.detector.pause).toHaveBeenCalledOnce()
  })

  it("lets the detector go when it stops", async () => {
    const { listener, detector, heard, events, frames } = await start()
    listener.resume()
    events.onSpeechStart()
    frames(1000, 0.9, LOUD)
    listener.stop()

    expect(heard).toEqual([])
    expect(detector.destroy).toHaveBeenCalledOnce()
  })
})
