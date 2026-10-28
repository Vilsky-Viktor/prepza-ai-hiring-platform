import { COUNTDOWN_WARNING_SECONDS } from "@/constants/interviews"

/** When a question's countdown turns red: its last COUNTDOWN_WARNING_SECONDS, or its last third
 * when that's shorter, so a short question isn't red the whole time. */
export function warningSeconds(questionSeconds: number) {
  return Math.min(
    COUNTDOWN_WARNING_SECONDS,
    Math.max(1, Math.floor(questionSeconds / 3))
  )
}

/** Seconds as a clock shows them: minutes and two-digit seconds ("1:05"). */
export function clock(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const rest = String(seconds % 60).padStart(2, "0")

  return `${minutes}:${rest}`
}
