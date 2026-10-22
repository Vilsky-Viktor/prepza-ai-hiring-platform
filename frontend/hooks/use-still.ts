"use client"

import { useSyncExternalStore } from "react"

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)"

function subscribe(change: () => void) {
  const query = window.matchMedia(REDUCED_MOTION)
  query.addEventListener("change", change)

  return () => query.removeEventListener("change", change)
}

/** Whether the landing's moving pictures stand still: the visitor asked for reduced motion. */
export function useStill() {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(REDUCED_MOTION).matches,
    () => false
  )
}
