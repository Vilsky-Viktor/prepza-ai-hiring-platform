import { splitInlineCode } from "@/lib/question-text"

export function InlineText({ text }: { text: string | null }) {
  if (!text) {
    return null
  }

  return splitInlineCode(text).map((piece, index) =>
    piece.code ? (
      <code
        key={index}
        className="rounded bg-surface px-1.5 py-0.5 font-mono text-[0.85em] font-normal"
      >
        {piece.text}
      </code>
    ) : (
      piece.text
    )
  )
}
