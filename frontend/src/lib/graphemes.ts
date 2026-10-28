// Text counted as people see it: by grapheme (a letter with its marks, an emoji, a Hindi or Thai
// cluster), never by UTF-16 unit, which splits them (.claude/rules/nextjs.md).
const segmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" })

/** The graphemes of `text`, in order. */
export function graphemes(text: string) {
  return Array.from(segmenter.segment(text), (part) => part.segment)
}

/** The first grapheme of `text`, as an initial; empty for empty text. */
export function firstGrapheme(text: string) {
  return segmenter.segment(text)[Symbol.iterator]().next().value?.segment ?? ""
}

/** The first `count` graphemes of `text`: a text typed so far. */
export function sliceGraphemes(text: string, count: number) {
  return graphemes(text).slice(0, count).join("")
}
