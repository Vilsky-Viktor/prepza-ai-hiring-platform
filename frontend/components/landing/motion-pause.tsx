"use client"

import { PauseIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import {
  createContext,
  useContext,
  useState,
  useSyncExternalStore,
} from "react"

import { IconButton } from "@/components/icon-button"

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)"

const MotionPause = createContext<{
  paused: boolean
  toggle: () => void
} | null>(null)

/** The landing page's moving pictures, which its pause button stops (WCAG 2.2.2: anything that
 * moves on its own for more than 5 seconds can be paused). Paused, they show what they show with
 * reduced motion: a complete, still frame; the `motion-reduce` variant and the reset in
 * animations.css apply inside `data-motion="paused"` too. */
export function MotionPauseProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [paused, setPaused] = useState(false)

  return (
    <MotionPause value={{ paused, toggle: () => setPaused(!paused) }}>
      <div data-motion={paused ? "paused" : undefined}>{children}</div>
    </MotionPause>
  )
}

/** The button that pauses the landing's moving pictures and plays them again. Not shown with
 * reduced motion, where nothing moves. */
export function MotionPauseButton() {
  const t = useTranslations("landing")
  const motion = useContext(MotionPause)

  if (!motion) {
    return null
  }

  return (
    <IconButton
      label={t("pauseMotion")}
      pressed={motion.paused}
      onClick={motion.toggle}
      className="size-11 rounded-full motion-reduce:hidden"
    >
      <PauseIcon aria-hidden className="size-6" />
    </IconButton>
  )
}

function subscribe(change: () => void) {
  const query = window.matchMedia(REDUCED_MOTION)
  query.addEventListener("change", change)

  return () => query.removeEventListener("change", change)
}

/** Whether moving pictures stand still: the visitor asked for reduced motion, or paused them. */
export function useStill() {
  const paused = useContext(MotionPause)?.paused ?? false
  const reduced = useSyncExternalStore(
    subscribe,
    () => window.matchMedia(REDUCED_MOTION).matches,
    () => false
  )

  return paused || reduced
}
