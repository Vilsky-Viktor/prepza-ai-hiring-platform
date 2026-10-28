"use client"

import { useEffect, useSyncExternalStore } from "react"

import { pageKey, registerPageKey, subscribePageKey } from "@/lib/page-key"
import type { PageHelpKey } from "@/types/page-help"

/** Registers the page on screen by its guide's key, while it's shown. */
export function usePageKey(key: PageHelpKey) {
  useEffect(() => registerPageKey(key), [key])
}

/** The key of the page on screen, or null (none registered). */
export function useCurrentPageKey() {
  return useSyncExternalStore(subscribePageKey, pageKey, () => null)
}
