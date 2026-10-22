import type { ReactNode } from "react"

// A message wraps each value people typed (a name, a company, an email, a title) in a `<bdi>`
// tag, so a name in another script keeps its own direction and doesn't reorder the sentence's
// punctuation and numbers around it.

/** For `t.rich`, where the message is shown as content: the value in a `<bdi>` element. */
export const bdi = {
  bdi: (chunks: ReactNode) => <bdi>{chunks}</bdi>,
}

/** For `t.markup`, where a plain string is needed (an `aria-label`, a title, a page's metadata):
 * the value between FIRST STRONG ISOLATE and POP DIRECTIONAL ISOLATE, which do the same. */
export const bdiText = {
  bdi: (chunks: string) => `\u2068${chunks}\u2069`,
}

/** `text` without the isolating marks `bdiText` adds, for where they can't be shown (a picture). */
export function withoutIsolates(text: string) {
  return text.replace(/[\u2068\u2069]/g, "")
}
