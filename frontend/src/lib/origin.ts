import { useSyncExternalStore } from "react"

function subscribe() {
  return () => {}
}

/** The site's origin in the browser; empty while rendering on the server. */
export function useOrigin() {
  return useSyncExternalStore(
    subscribe,
    () => window.location.origin,
    () => ""
  )
}
