import { POLL_BACKOFF, POLL_MAX_MS, POLL_MIN_MS } from "@/constants/generation"

/** The wait before the next poll: the shortest after a change, longer after each poll that
 * brought none, up to the longest. */
export function nextPollDelay(delay: number, changed: boolean) {
  return changed ? POLL_MIN_MS : Math.min(delay * POLL_BACKOFF, POLL_MAX_MS)
}
