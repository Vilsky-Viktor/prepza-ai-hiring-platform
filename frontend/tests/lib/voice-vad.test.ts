import { readFileSync } from "node:fs"
import { createRequire } from "node:module"
import { dirname, join } from "node:path"

import { afterEach, beforeEach, expect, it, vi } from "vitest"

import { VAD_FILES, VAD_OPTIONS } from "@/config/voice"
import { micDetector } from "@/lib/voice-vad"

const made = vi.hoisted(() => ({ options: {} as Record<string, unknown> }))
const vad = vi.hoisted(() => ({
  start: vi.fn(async () => undefined),
  pause: vi.fn(async () => undefined),
  destroy: vi.fn(async () => undefined),
}))

vi.mock("@ricky0123/vad-web", () => ({
  MicVAD: {
    new: async (options: Record<string, unknown>) => {
      made.options = options

      return vad
    },
  },
}))

beforeEach(() => {
  vi.spyOn(console, "warn").mockImplementation(() => undefined)
})

afterEach(() => {
  vi.clearAllMocks()
})

function events() {
  return {
    onFrame: vi.fn(),
    onSpeechStart: vi.fn(),
    onSpeechEnd: vi.fn(),
    onMisfire: vi.fn(),
  }
}

it("listens to the microphone already open and never stops it", async () => {
  const context = {} as AudioContext
  const stream = { getTracks: vi.fn() } as unknown as MediaStream
  const given = events()
  await micDetector(context, stream)(given)
  const options = made.options as {
    audioContext: AudioContext
    getStream: () => Promise<MediaStream>
    pauseStream: (stream: MediaStream) => Promise<void>
    resumeStream: (stream: MediaStream) => Promise<MediaStream>
    onFrameProcessed: (p: { isSpeech: number }, frame: Float32Array) => void
  }

  expect(options).toMatchObject({
    ...VAD_OPTIONS,
    startOnLoad: false,
    baseAssetPath: VAD_FILES,
  })
  expect(options.audioContext).toBe(context)
  expect(await options.getStream()).toBe(stream)
  expect(await options.resumeStream(stream)).toBe(stream)
  await options.pauseStream(stream)
  expect(stream.getTracks).not.toHaveBeenCalled()

  const frame = new Float32Array(512)
  options.onFrameProcessed({ isSpeech: 0.8 }, frame)
  expect(given.onFrame).toHaveBeenCalledWith(0.8, frame)
})

it("runs its steps one after another, and a failed one breaks none after it", async () => {
  const detector = await micDetector(
    {} as AudioContext,
    {} as MediaStream
  )(events())
  const order: string[] = []
  vad.start.mockImplementationOnce(async () => {
    await Promise.resolve()
    order.push("started")
    throw new Error("no sound")
  })
  vad.pause.mockImplementationOnce(async () => {
    order.push("paused")
  })

  void detector.start()
  await detector.pause()

  expect(order).toEqual(["started", "paused"])
})

// public/vad/ is copied from the installed packages under their versions (scripts/copy-vad.mjs).
it("names the folder of the installed detector's versions", () => {
  const require = createRequire(import.meta.url)
  const version = (folder: string) =>
    JSON.parse(readFileSync(join(folder, "package.json"), "utf8")).version
  const vadWeb = dirname(require.resolve("@ricky0123/vad-web/package.json"))
  const ort = dirname(
    dirname(
      createRequire(join(vadWeb, "package.json")).resolve("onnxruntime-web")
    )
  )

  expect(VAD_FILES).toBe(`/vad/${version(vadWeb)}-${version(ort)}/`)
})
