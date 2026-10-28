"use client"

import { useSyncExternalStore } from "react"

function subscribe() {
  return () => {}
}

/** An email address put together only in the browser: the server's HTML doesn't hold it, so
bots that read pages without running scripts don't find it. */
export function ProtectedEmail({
  user,
  domain,
}: {
  user: string
  domain: string
}) {
  const browser = useSyncExternalStore(
    subscribe,
    () => true,
    () => false
  )

  if (!browser) {
    return null
  }

  const address = `${user}@${domain}`

  return (
    <a
      href={`mailto:${address}`}
      className="text-foreground underline underline-offset-4"
    >
      {address}
    </a>
  )
}
