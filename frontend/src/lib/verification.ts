import { toast } from "sonner"

import { ApiError, apiErrorMessage } from "@/lib/api"

/** A superadmin's approve or decline that failed: a request decided or changed meanwhile (409)
 * says so and reloads the list; anything else says it didn't work. */
export function decisionFailed(
  error: unknown,
  texts: { changed: string; failed: string },
  refresh: () => void
) {
  if (error instanceof ApiError && error.status === 409) {
    toast.error(texts.changed)
    refresh()

    return
  }

  toast.error(apiErrorMessage(error, texts.failed))
}
