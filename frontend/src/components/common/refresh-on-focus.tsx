"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

/** Reloads the page's server data when its tab is back in view, so balances shown there catch up
 * with an automatic top-up, or a payment in another tab, and count up to it. */
export function RefreshOnFocus() {
  const router = useRouter()

  useEffect(() => {
    const refresh = () => router.refresh()
    window.addEventListener("focus", refresh)

    return () => window.removeEventListener("focus", refresh)
  }, [router])

  return null
}
