import { cn } from "cn"
import { BookmarkIcon } from "lucide-react"

/** An interview's pinned note as one muted line under its title (on its page and in the
 * interviews list), cut at the line's end: whom it's for, at a glance. */
export function PinnedNote({
  text,
  className,
}: {
  text: string
  className?: string
}) {
  return (
    <span
      data-testid="pinned-note"
      className={cn(
        "flex min-w-0 items-center gap-1.5 text-muted-foreground",
        className
      )}
    >
      <BookmarkIcon aria-hidden className="size-4 shrink-0" />
      <span dir="auto" className="truncate">
        {text}
      </span>
    </span>
  )
}
