import { graphemes } from "@/lib/graphemes"

/** The padding a field keeps at one side for a sign or unit inside it ("$", "px"), by its length;
 * none without one. */
export function adornmentRoom(text?: string) {
  if (!text) {
    return undefined
  }

  return `calc(2rem + ${graphemes(text).length}ch)`
}
