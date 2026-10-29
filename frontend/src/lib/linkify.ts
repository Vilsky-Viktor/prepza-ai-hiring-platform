// A web address in typed text: http(s) only, up to a space; trailing punctuation stays text.
const URL_PATTERN = /https?:\/\/[^\s<>"]+[^\s<>".,;:!?)\]}'"]/g

/** Typed text in pieces, each plain text or a web address to show as a link. Only http and
 * https addresses become links, so a typed `javascript:` stays text; nothing is ever HTML. */
export function linkParts(text: string): { text: string; url?: string }[] {
  const parts: { text: string; url?: string }[] = []
  let last = 0

  for (const match of text.matchAll(URL_PATTERN)) {
    const start = match.index ?? 0

    if (start > last) {
      parts.push({ text: text.slice(last, start) })
    }

    parts.push({ text: match[0], url: match[0] })
    last = start + match[0].length
  }

  if (last < text.length) {
    parts.push({ text: text.slice(last) })
  }

  return parts
}
