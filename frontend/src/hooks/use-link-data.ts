"use client"

import { useEffect, useState } from "react"

import { apiFetch, serviceRefusal } from "@/lib/api"
import { linkFailure } from "@/lib/link-status"

// What a page opened from a link (an invite, a job link, an unsubscribe link) knows of it: still
// loading, gone (the API says it doesn't exist), not loaded (anything else: the network, a
// busy or paused service), or there.
export type LinkStatus = "loading" | "missing" | "failed" | "ready"

/** Reads `path` once `path` is set, and again when `refresh` changes (a sign-in) or on retry().
 * A link is called invalid only when the API says it's gone; anything else can be retried.
 * `gone` is the API's reason when it said why (410: an invite that expired, an interview no
 * longer available), in the reader's language. */
export function useLinkData<T>(path: string | null, refresh?: unknown) {
  const [data, setData] = useState<T | null>(null)
  const [status, setStatus] = useState<LinkStatus>("loading")
  const [attempt, setAttempt] = useState(0)
  const [gone, setGone] = useState<string | null>(null)

  useEffect(() => {
    if (path === null) {
      return
    }

    let current = true

    apiFetch<T>(path)
      .then((found) => {
        if (current) {
          setData(found)
          setStatus("ready")
        }
      })
      .catch((error) => {
        if (current) {
          setStatus(linkFailure(error))
          setGone(serviceRefusal(error, [410]))
        }
      })

    return () => {
      current = false
    }
  }, [path, refresh, attempt])

  function retry() {
    setStatus("loading")
    setAttempt((count) => count + 1)
  }

  return { data, status, retry, gone }
}
