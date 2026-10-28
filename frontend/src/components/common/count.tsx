import type { ReactNode } from "react"

/** "done / total", in that order in right-to-left text too (numbers stay left to right). */
export function Count({ done, total }: { done: ReactNode; total: ReactNode }) {
  return (
    <span dir="ltr" data-testid="count">
      {done} / {total}
    </span>
  )
}
