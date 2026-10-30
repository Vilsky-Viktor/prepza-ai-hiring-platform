import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  IDLE_RESTART_MS,
  LEVEL_EVERY_MS,
  SPEECH_END_MS,
  SPEECH_START_MS,
} from "@/config/voice"
import { level, listen } from "@/lib/voice-listening"

describe("level", () => {
  it("is the sound's root mean square", () => {
    expect(level(new Float32Array([0.5, -0.5, 0.5, -0.5]))).toBeCloseTo(0.5)
    expect(level(new Float32Array(8))).toBe(0)
  })
})

describe("listen", () => {
  // The microphone's level now, as the fake analyser reads it.
  let loudness: number
  let recorders: FakeRecorder[]

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

  const context = {
    createAnalyser: () => ({
      fftSize: 0,
      getFloatTimeDomainData: (samples: Float32Array) => samples.fill(loudness),
      disconnect: () => undefined,
    }),
    createMediaStreamSource: () => ({ connect: () => undefined }),
  } as unknown as AudioContext

  function start() {
    const heard: { audio: Blob; voicedMs: number }[] = []
    const onSpeechStart = vi.fn()
    const listener = listen(
      context,
      {} as MediaStream,
      "audio/webm;codecs=opus",
      {
        onSpeechStart,
        onSpeech: (audio, voicedMs) => heard.push({ audio, voicedMs }),
      }
    )

    return { listener, heard, onSpeechStart }
  }

  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal("window", globalThis)
    vi.stubGlobal("MediaRecorder", FakeRecorder)
    loudness = 0
    recorders = []
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("sends a stretch of speech once it ends, with how long it was voiced", () => {
    const { listener, heard, onSpeechStart } = start()
    loudness = 0.1
    vi.advanceTimersByTime(SPEECH_START_MS + 1000)

    expect(onSpeechStart).toHaveBeenCalledOnce()
    expect(heard).toEqual([])

    loudness = 0
    vi.advanceTimersByTime(SPEECH_END_MS)

    expect(heard).toHaveLength(1)
    expect(heard[0].audio.type).toBe("audio/webm")
    expect(heard[0].voicedMs).toBe(SPEECH_START_MS + 1000)
    listener.stop()
  })

  it("never sends silence, recording afresh while nobody speaks", () => {
    const { listener, heard, onSpeechStart } = start()
    vi.advanceTimersByTime(IDLE_RESTART_MS * 3)

    expect(heard).toEqual([])
    expect(onSpeechStart).not.toHaveBeenCalled()
    expect(recorders.length).toBeGreaterThan(2)
    listener.stop()
  })

  it("ignores a sound too short to be speech", () => {
    const { listener, onSpeechStart } = start()
    loudness = 0.1
    vi.advanceTimersByTime(SPEECH_START_MS - LEVEL_EVERY_MS)
    loudness = 0
    vi.advanceTimersByTime(SPEECH_END_MS * 2)

    expect(onSpeechStart).not.toHaveBeenCalled()
    listener.stop()
  })

  it("hears nothing while paused and starts afresh on resume", () => {
    const { listener, heard, onSpeechStart } = start()
    listener.pause()
    loudness = 0.1
    vi.advanceTimersByTime(SPEECH_START_MS * 4)

    expect(onSpeechStart).not.toHaveBeenCalled()

    listener.resume()
    vi.advanceTimersByTime(SPEECH_START_MS)
    loudness = 0
    vi.advanceTimersByTime(SPEECH_END_MS)

    expect(onSpeechStart).toHaveBeenCalledOnce()
    expect(heard).toHaveLength(1)
    listener.stop()
  })

  it("waits for a resume after sending, so one answer is sent at a time", () => {
    const { listener, heard } = start()
    loudness = 0.1
    vi.advanceTimersByTime(SPEECH_START_MS)
    loudness = 0
    vi.advanceTimersByTime(SPEECH_END_MS)
    loudness = 0.1
    vi.advanceTimersByTime(SPEECH_START_MS * 4)
    loudness = 0
    vi.advanceTimersByTime(SPEECH_END_MS)

    expect(heard).toHaveLength(1)
    listener.stop()
  })
})
