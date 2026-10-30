import { useEffect, useRef } from "react"

import type { Meter } from "@/lib/voice-meters"

// The levels the real meter reads while someone speaks: Mira's from the speakers, the
// candidate's from the microphone (config/voice.ts turns them into the waves' heights).
const SPEAKER_LEVEL = 0.2
const MIC_LEVEL = 0.06

/** How loud speech is at `time` (milliseconds), 0 to 1: syllables rising and falling, in
 * louder and quieter phrases, never silent while someone talks. */
export function speechLevel(time: number) {
  const syllables = 0.55 + 0.45 * Math.sin(time / 95) * Math.sin(time / 37)
  const phrases = 0.65 + 0.35 * Math.sin(time / 610)

  return Math.max(0, syllables) * phrases
}

/** A stand-in for the voice screen's meter (lib/voice-meters.ts) for a landing demo, for the
 * real useVoiceWaves: speech-like levels from Mira while `mira` talks and from the microphone
 * while `you` do, silence otherwise. */
export function useDemoMeter(mira: boolean, you: boolean) {
  const meter = useRef<Meter | null>(null)

  useEffect(() => {
    meter.current = {
      speaker: () =>
        mira ? SPEAKER_LEVEL * speechLevel(performance.now()) : 0,
      mic: () => (you ? MIC_LEVEL * speechLevel(performance.now() + 4000) : 0),
    }
  }, [mira, you])

  return meter
}
