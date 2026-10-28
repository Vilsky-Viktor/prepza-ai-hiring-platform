import { ACTION_FILTERS } from "@/config/action-log"

/** The action log's filters the address gives (member, group of actions, from and to), for
 * the API; empty ones are left out. */
export function actionFilters(
  asked: Record<string, string | undefined>
): URLSearchParams {
  const filters = new URLSearchParams()

  for (const name of ACTION_FILTERS) {
    const value = asked[name]

    if (value) {
      filters.set(name, value)
    }
  }

  return filters
}
