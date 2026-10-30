"use client"

import { type RefObject, useEffect, useRef } from "react"

import {
  FLAT_BAR,
  WAVE_EASE,
  WAVE_GAIN,
  YOU_WAVE_FLOOR,
  YOU_WAVE_GAIN,
} from "@/config/voice"
import { useStill } from "@/hooks/use-still"
import type { Meter } from "@/lib/voice-meters"

/** Sets each bar in `wave` to `height` (0 to 1), the middle bars highest, rippling a little over
 * time. */
function paint(wave: HTMLElement | null, height: number, time: number) {
  if (!wave) {
    return
  }

  const count = wave.children.length

  for (let index = 0; index < count; index += 1) {
    const centre = 1 - Math.abs(index / Math.max(count - 1, 1) - 0.5) * 1.2
    const ripple = 0.75 + 0.25 * Math.sin(time / 140 + index * 0.9)
    const bar = Math.min(1, height * centre * ripple)
    const element = wave.children[index] as HTMLElement
    element.style.transform = `scaleY(${Math.max(FLAT_BAR, bar)})`
  }
}

/** The candidate's wave's height for the microphone's `level` (config/voice.ts). */
export function voiceHeight(level: number) {
  return level < YOU_WAVE_FLOOR ? 0 : Math.sqrt(level * YOU_WAVE_GAIN)
}

/** Moves the voice screen's two waves with the real sound: `mira` with what Mira says, `you` with
 * what the microphone hears (flat while `quiet`: while Mira speaks). One animation
 * frame loop writing transforms only, stopped while the page is hidden and never started with
 * reduced motion, where both stay flat lines. Returns the refs for the two waves' bar
 * containers. */
export function useVoiceWaves(meter: RefObject<Meter | null>, quiet: boolean) {
  const still = useStill()
  const mira = useRef<HTMLDivElement>(null)
  const you = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (still) {
      return
    }

    const miraWave = mira.current
    const youWave = you.current
    let frame = 0
    let spoken = 0
    let heard = 0

    function draw(time: number) {
      const levels = meter.current
      spoken += ((levels?.speaker() ?? 0) - spoken) * WAVE_EASE
      heard += ((levels && !quiet ? levels.mic() : 0) - heard) * WAVE_EASE
      paint(miraWave, spoken * WAVE_GAIN, time)
      paint(youWave, voiceHeight(heard), time)
      frame = window.requestAnimationFrame(draw)
    }

    function run() {
      window.cancelAnimationFrame(frame)

      if (!document.hidden) {
        frame = window.requestAnimationFrame(draw)
      }
    }

    run()
    document.addEventListener("visibilitychange", run)

    return () => {
      window.cancelAnimationFrame(frame)
      document.removeEventListener("visibilitychange", run)
      paint(miraWave, 0, 0)
      paint(youWave, 0, 0)
    }
  }, [still, quiet, meter])

  return { mira, you }
}
