import type { ReactNode } from "react"

/** A search and the list under it as one block: the search's field (InputAction) on top with
 * square bottom corners, the list's box (LIST_BOX) or its empty state (LIST_EMPTY) straight under
 * it with square top corners, through the `searched` variant. */
export function SearchedList({ children }: { children: ReactNode }) {
  return <div data-slot="searched-list">{children}</div>
}
