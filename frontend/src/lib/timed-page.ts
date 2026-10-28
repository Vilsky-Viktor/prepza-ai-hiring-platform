// Whether a timed question's page never got to its questions (signed out, not found, failed), so
// the site's header and footer come back (components/common/not-on-timed-page.tsx).
let over = false
const listeners = new Set<() => void>()

export function setTimedPageOver(value: boolean) {
  if (value === over) {
    return
  }

  over = value
  listeners.forEach((listener) => listener())
}

export function subscribeTimedPageOver(listener: () => void) {
  listeners.add(listener)

  return () => listeners.delete(listener)
}

export function timedPageOver() {
  return over
}
