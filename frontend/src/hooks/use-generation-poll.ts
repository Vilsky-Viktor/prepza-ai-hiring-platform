"use client"

import { useEffect, useEffectEvent } from "react"

import { ACTIVE_STATUSES, POLL_MIN_MS } from "@/constants/generation"
import { ApiError, apiFetch } from "@/lib/api"
import { nextPollDelay } from "@/lib/poll"
import type { Generation } from "@/types/generation"

type Polled = {
  status?: Generation["status"] | null
  progress?: Generation["progress"]
}

/** Polls a generation's `path` while it's queued or running: soon after a change, longer after
 * each poll that brought none (lib/poll.ts). A hidden tab doesn't poll; it polls again once it
 * shows. An answer that it isn't there (403, 404, 422) calls `onMissing` and stops; any other
 * failure (network, a restart, a rate limit) tries again. No `path` polls nothing; a new
 * `round` starts again, after the caller restarted the generation. */
export function useGenerationPoll<T extends Polled>(
  path: string | null,
  round: number,
  onValue: (value: T) => void,
  onMissing?: () => void
) {
  const received = useEffectEvent(onValue)
  const missing = useEffectEvent(() => onMissing?.())

  useEffect(() => {
    if (!path) {
      return
    }

    const polled = path
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    let delay = POLL_MIN_MS
    // The last poll's status and progress, to tell whether anything moved.
    let last = ""
    // Set while a poll is due but the tab is hidden; it runs once the tab shows again.
    let paused = false

    function schedule() {
      if (document.hidden) {
        paused = true

        return
      }

      timer = setTimeout(load, delay)
    }

    function resume() {
      if (document.hidden || !paused) {
        return
      }

      paused = false
      delay = POLL_MIN_MS
      load()
    }

    async function load() {
      try {
        const next = await apiFetch<T>(polled)

        if (!active) {
          return
        }

        received(next)
        const seen = JSON.stringify([next.status, next.progress])
        const changed = seen !== last
        last = seen

        if (next.status && ACTIVE_STATUSES.includes(next.status)) {
          delay = nextPollDelay(delay, changed)
          schedule()
        }
      } catch (error) {
        if (!active) {
          return
        }

        if (
          error instanceof ApiError &&
          [403, 404, 422].includes(error.status)
        ) {
          missing()

          return
        }

        delay = nextPollDelay(delay, false)
        schedule()
      }
    }

    load()
    document.addEventListener("visibilitychange", resume)

    return () => {
      active = false
      clearTimeout(timer)
      document.removeEventListener("visibilitychange", resume)
    }
  }, [path, round])
}
