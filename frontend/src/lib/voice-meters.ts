import { SOUND_WAIT_MS } from "@/config/voice"
import { level } from "@/lib/voice-listening"

// The levels the voice screen's waves show, 0 to 1, read on each animation frame.
export type Meter = { speaker: () => number; mic: () => number }

/** Measures what Mira says and what the microphone hears, for the waves only: listening keeps
 * its own measure. The player plays to the speakers itself; the meter only reads a copy of its
 * sound (`captureStream`, renewed each time a clip starts), so the waves never stand between
 * Mira and the speakers. Without `captureStream` her wave stays flat. */
export function meters(
  context: AudioContext,
  player: HTMLAudioElement,
  stream: MediaStream
): Meter {
  const speaker = context.createAnalyser()
  const mic = context.createAnalyser()
  speaker.fftSize = 512
  mic.fftSize = 512
  context.createMediaStreamSource(stream).connect(mic)
  const capturing = player as HTMLAudioElement & {
    captureStream?: () => MediaStream
  }
  let copy: MediaStreamAudioSourceNode | null = null

  player.addEventListener("playing", () => {
    const sound = capturing.captureStream?.()

    if (!sound || sound.getAudioTracks().length === 0) {
      return
    }

    copy?.disconnect()
    copy = context.createMediaStreamSource(sound)
    copy.connect(speaker)
  })

  const samples = new Float32Array(512)

  function read(analyser: AnalyserNode) {
    analyser.getFloatTimeDomainData(samples)

    return level(samples)
  }

  return { speaker: () => read(speaker), mic: () => read(mic) }
}

/** Whether `context` may play sound: browsers allow it only after a tap on the page, which the
 * start page's button gives; a reloaded page needs another. */
export async function soundAllowed(context: AudioContext) {
  if (context.state === "suspended") {
    await Promise.race([
      context.resume(),
      new Promise((done) => window.setTimeout(done, SOUND_WAIT_MS)),
    ])
  }

  return context.state === "running"
}
