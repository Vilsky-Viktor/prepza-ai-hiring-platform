import { ApiError } from "@/lib/api"

/** A "Top up" button for the toast when the error is a lack of credits (402). */
export function topUpAction(
  error: unknown,
  label: string,
  onClick: () => void
) {
  return error instanceof ApiError && error.status === 402
    ? { action: { label, onClick } }
    : undefined
}
