import type { GenerationStatus } from "@/types/generation"

// A generation is polled every POLL_MIN_MS while it moves; each poll that brings no change waits
// POLL_BACKOFF times longer, up to POLL_MAX_MS. A hidden tab doesn't poll.
export const POLL_MIN_MS = 2000
export const POLL_MAX_MS = 10000
export const POLL_BACKOFF = 1.5
export const ACTIVE_STATUSES: GenerationStatus[] = ["queued", "running"]
