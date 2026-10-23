import { ChevronRightIcon } from "lucide-react"

import { LocalizedLink } from "@/components/localized-link"
import type { ContentPage } from "@/lib/content"
import { LIST_BOX, ROW_HOVER } from "@/constants/lists"

/** A hub's pages as one list, like the companies list: each title with its description (in its
 * own language), opening the page under `base` in the address's language. */
export function ContentList({
  pages,
  base,
}: {
  pages: ContentPage[]
  base: string
}) {
  return (
    <ul className={LIST_BOX}>
      {pages.map((page) => (
        <li key={page.slug} lang={page.language}>
          <LocalizedLink
            href={`${base}/${page.slug}`}
            className={`flex items-center gap-6 p-6 ${ROW_HOVER}`}
          >
            <span className="min-w-0 flex-1 space-y-1">
              <span className="block text-lg font-medium">{page.title}</span>
              <span className="block text-base text-muted-foreground">
                {page.description}
              </span>
            </span>
            <ChevronRightIcon
              aria-hidden
              className="size-5 shrink-0 text-muted-foreground rtl:-scale-x-100"
            />
          </LocalizedLink>
        </li>
      ))}
    </ul>
  )
}
