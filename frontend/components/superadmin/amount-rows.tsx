import Link from "next/link"
import type { ReactNode } from "react"

import { Dotted } from "@/components/dot"
import { LIST_BOX, ROW_HOVER } from "@/constants/lists"

export type AmountRow = {
  key: string
  title: ReactNode
  // Facts under the title, a dot between each two.
  details?: ReactNode[]
  amount: ReactNode
  // A row that opens a support page.
  href?: string
}

const ROW = "flex items-center justify-between gap-4 p-6"

/** A titled list of the AI costs tab: each row its name and facts on the left, its amount on the
 * right; a row with a link opens it. Nothing to show: the empty text, in the list's place. */
export function AmountRows({
  title,
  rows,
  empty,
}: {
  title: string
  rows: AmountRow[]
  empty: string
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-medium">{title}</h2>
      {rows.length === 0 ? (
        <p className="py-8 text-center text-muted-foreground">{empty}</p>
      ) : (
        <ul className={LIST_BOX}>
          {rows.map((row) => {
            const content = (
              <>
                <span className="min-w-0 space-y-1">
                  <span className="block font-medium break-words">
                    {row.title}
                  </span>
                  {row.details && row.details.length > 0 && (
                    <span
                      className="block text-sm text-muted-foreground"
                      data-testid="amount-details"
                    >
                      <Dotted items={row.details} />
                    </span>
                  )}
                </span>
                <span className="shrink-0 text-lg tabular-nums">
                  {row.amount}
                </span>
              </>
            )

            return (
              <li key={row.key} data-testid={`amount-${row.key}`}>
                {row.href ? (
                  <Link href={row.href} className={`${ROW} ${ROW_HOVER}`}>
                    {content}
                  </Link>
                ) : (
                  <div className={ROW}>{content}</div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
