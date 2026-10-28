import { ALWAYS_FILLED_TYPES } from "@/config/floating-label"
import { graphemes } from "@/lib/graphemes"

/** Whether an input of this type always shows something (a date's "dd/mm/yyyy"), so its label
 * stays raised even while it's empty. */
export function alwaysFilled(type?: string) {
  return ALWAYS_FILLED_TYPES.includes(type ?? "")
}

/** The padding a field keeps at one side for a sign or unit inside it ("$", "px"), by its length;
 * none without one. */
export function adornmentRoom(text?: string) {
  if (!text) {
    return undefined
  }

  return `calc(2rem + ${graphemes(text).length}ch)`
}
