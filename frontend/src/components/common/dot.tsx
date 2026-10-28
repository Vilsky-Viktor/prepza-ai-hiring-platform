import { Fragment, type ReactNode } from "react"

import { DOT_CLASS, WRITTEN_DOT } from "@/config/dot"

/** The separator alone; screen readers hear a comma. */
export function Dot({ className = "" }: { className?: string }) {
  return (
    <>
      <span aria-hidden className={`${DOT_CLASS} ${className}`} />
      <span className="sr-only">, </span>
    </>
  )
}

/** Facts in a row with a dot between each two; empty ones are left out. */
export function Dotted({ items }: { items: ReactNode[] }) {
  const shown = items.filter(
    (item) =>
      item !== null && item !== undefined && item !== false && item !== ""
  )

  return (
    <>
      {shown.map((item, index) => (
        <Fragment key={index}>
          {index > 0 && <Dot />}
          {item}
        </Fragment>
      ))}
    </>
  )
}

/** A translated text that lists facts with " · " ("passed · passing grade 70%"), its dots
 * drawn as the separator. */
export function DottedText({ text }: { text: string }) {
  return <Dotted items={text.split(WRITTEN_DOT)} />
}
