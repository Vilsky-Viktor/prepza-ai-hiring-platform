import type { ReactNode } from "react"

// A message wraps the date it names in a `<time>` tag, so the date is a `<time>` element, which
// the site shows in italics (globals.css).

/** For `t.rich`: the message's date in a `<time>` element of the moment or day `iso`. */
export function timeTag(iso: string) {
  return {
    time: (chunks: ReactNode) => <time dateTime={iso}>{chunks}</time>,
  }
}
