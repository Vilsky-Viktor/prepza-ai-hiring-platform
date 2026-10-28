"use client"

import { useRef } from "react"

/** Runs an action only once the last one finished: a second submit while one is running (a
 * quick second ⌘/Ctrl+Enter, which a disabled button doesn't stop) is ignored, so nothing is
 * sent twice. */
export function useOneAtATime() {
  const running = useRef(false)

  return async (action: () => Promise<void>) => {
    if (running.current) {
      return
    }

    running.current = true

    try {
      await action()
    } finally {
      running.current = false
    }
  }
}
