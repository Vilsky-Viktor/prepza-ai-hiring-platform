import { LEGAL_BANNER_KEY } from "@/constants/notifications"
import type { LegalChange } from "@/types/campaigns"

function storageKey(change: LegalChange) {
  return LEGAL_BANNER_KEY.replace("{document}", change.document).replace(
    "{version}",
    change.version
  )
}

/** The changes whose banner wasn't closed in this browser; all of them while the browser keeps
 * nothing. */
export function notClosed(changes: LegalChange[]) {
  return changes.filter((change) => {
    try {
      return localStorage.getItem(storageKey(change)) === null
    } catch {
      return true
    }
  })
}

/** Remembers in this browser that the change's banner was closed: for that version only. */
export function rememberClosed(change: LegalChange) {
  try {
    localStorage.setItem(storageKey(change), "closed")
  } catch {}
}
