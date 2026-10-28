import { MAX_RECONNECT_MS, RECONNECT_MS } from "@/config/notifications"
import { authHeaders } from "@/lib/api"

/** Keeps the bell's live stream open until `signal` aborts, calling onNew whenever a
 * notification comes, and onOpen each time it (re)connects so nothing missed meanwhile is lost.
 * A dropped stream (the server ends it every few minutes, a deploy, the network) reconnects by
 * itself; with `fresh`, the first connect reads the user's companies again. */
export async function watchNotifications(
  signal: AbortSignal,
  onOpen: () => void,
  onNew: () => void,
  fresh = false
) {
  let wait = RECONNECT_MS
  // Only the first connect asks for the companies fresh (right after joining one).
  let query = fresh ? "?fresh=true" : ""

  while (!signal.aborted) {
    try {
      const response = await fetch(`/api/notifications/me/stream${query}`, {
        headers: await authHeaders(),
        signal,
      })

      if (response.ok && response.body) {
        wait = RECONNECT_MS
        query = ""
        onOpen()
        const reader = response.body
          .pipeThrough(new TextDecoderStream())
          .getReader()

        while (true) {
          const { value, done } = await reader.read()

          if (done) {
            break
          }

          // Heartbeats are comments (": heartbeat"); only data lines announce something new.
          if (value.includes("data:")) {
            onNew()
          }
        }
      }
    } catch {
      // Aborted, or the network dropped: the loop decides whether to try again.
    }

    if (signal.aborted) {
      return
    }

    // Spread out, so tabs that lost their streams together (a deploy) don't all come back at
    // once.
    await new Promise((resolve) =>
      setTimeout(resolve, wait * (0.5 + Math.random()))
    )
    wait = Math.min(wait * 2, MAX_RECONNECT_MS)
  }
}
