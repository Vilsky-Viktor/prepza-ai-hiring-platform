import { keptCaseParts } from "@/lib/keep-case"

/** A title's or a button's text with its acronyms (ATS, PDF) and the names Slack and Mira (the
 * assistant's) as written, though titles and buttons are lowercase. */
export function KeepAcronyms({ text }: { text: string }) {
  return keptCaseParts(text).map((part, index) =>
    index % 2 ? (
      <span key={index} className="normal-case">
        {part}
      </span>
    ) : (
      part
    )
  )
}
