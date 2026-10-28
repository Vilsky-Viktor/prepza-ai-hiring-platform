"use client"

import { useEffect, useState } from "react"

import { COPIED_MS } from "@/config/layout"

/** Copies `id` to the clipboard; `copied` is true for COPIED_MS after, for a check mark. */
export function useCopyId(id: string) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) {
      return
    }

    const timer = setTimeout(() => setCopied(false), COPIED_MS)

    return () => clearTimeout(timer)
  }, [copied])

  async function copy() {
    await navigator.clipboard.writeText(id)
    setCopied(true)
  }

  return { copied, copy }
}
