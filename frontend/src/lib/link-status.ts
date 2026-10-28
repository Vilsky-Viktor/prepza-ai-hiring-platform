import { ApiError } from "@/lib/api"

// The API's answers that mean a link itself is no good (an invite, a job link, an unsubscribe
// link); anything else (the network, a busy or paused service) can be tried again.
const GONE = [404, 410]

/** Why a link's page couldn't load: the link is gone, or it can be tried again. */
export function linkFailure(error: unknown): "missing" | "failed" {
  return error instanceof ApiError && GONE.includes(error.status)
    ? "missing"
    : "failed"
}
