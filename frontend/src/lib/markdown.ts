import type { Options } from "react-markdown"

import { answerHref, inAppHref } from "@/lib/assistant"

// The markdown an assistant's answer may use: text, emphasis, lists, code and links. Anything
// else (images, tables, headings, raw HTML) shows as its text, or not at all.
const ELEMENTS = [
  "p",
  "br",
  "strong",
  "em",
  "ul",
  "ol",
  "li",
  "pre",
  "code",
  "a",
]

/** react-markdown's options for an answer: only ELEMENTS, no raw HTML, and links only to the
 * app's pages the panel knows, by their path (any other link keeps its text and loses its
 * address). */
export const ANSWER_MARKDOWN: Options = {
  allowedElements: ELEMENTS,
  unwrapDisallowed: true,
  skipHtml: true,
  urlTransform: (url) => answerHref(url),
}

/** react-markdown's options for a FAQ answer: plain text with links to the site's own pages
 * ("[pricing](/pricing)"); any other link, and anything else, shows as its text. */
export const FAQ_MARKDOWN: Options = {
  allowedElements: ["p", "a"],
  allowElement: (element) =>
    element.tagName !== "a" || !!element.properties.href,
  unwrapDisallowed: true,
  urlTransform: (url) => inAppHref(url),
}

/** A FAQ answer as plain text: each link becomes its text. */
export function plainAnswer(text: string) {
  return text.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
}
