import type { PageHelpKey } from "@/types/page-help"

// The key of the page on screen (its guide's), which every page registers (hooks/use-page-key.ts):
// the assistant's panel sends it with each message. None on the admin zone's pages.
let current: PageHelpKey | null = null
const listeners = new Set<() => void>()

function set(key: PageHelpKey | null) {
  current = key
  listeners.forEach((listener) => listener())
}

/** Registers `key` as the page on screen, until the returned function takes it back. */
export function registerPageKey(key: PageHelpKey) {
  set(key)

  return () => {
    // A page that came since keeps its own key.
    if (current === key) {
      set(null)
    }
  }
}

export function subscribePageKey(listener: () => void) {
  listeners.add(listener)

  return () => listeners.delete(listener)
}

export function pageKey() {
  return current
}
