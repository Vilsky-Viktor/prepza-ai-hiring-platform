"use client"

import { usePageKey } from "@/hooks/use-page-key"
import type { PageHelpKey } from "@/types/page-help"

/** Registers a page without an info button by its guide's key, for the assistant; shows
 * nothing. A page with an info button registers through it (PageHelp). */
export function PageKey({ page }: { page: PageHelpKey }) {
  usePageKey(page)

  return null
}
