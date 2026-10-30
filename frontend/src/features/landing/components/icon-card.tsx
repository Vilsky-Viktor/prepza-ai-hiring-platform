import { cn } from "cn"
import type { LucideIcon } from "lucide-react"

import { KeepAcronyms } from "@/components/common/keep-acronyms"

// A list of cards on phones: each the screen's full width, edge to edge, one under another.
export const PHONE_CARDS = "max-sm:-mx-6 max-sm:gap-3"

/** A grey landing card: a title ending with the logo's blue dot, a short line and its icon in
 * the top corner; ringed, with its icon blue, while `lit`. On phones, square, its text in line
 * with the page's, for a list of them edge to edge (PHONE_CARDS). */
export function IconCard({
  icon: Icon,
  title,
  lit = false,
  className,
  children,
}: {
  icon: LucideIcon
  title: string
  lit?: boolean
  // Its fill, when not the site's grey.
  className?: string
  children: React.ReactNode
}) {
  return (
    <li
      data-testid="icon-card"
      data-lit={lit || undefined}
      className={cn(
        "relative flex flex-col justify-center gap-1.5 bg-surface px-6 py-5 pe-16 transition-shadow duration-300 sm:rounded-xl sm:p-5 sm:pe-16",
        lit && "border-primary-gradient",
        className
      )}
    >
      <Icon
        className={cn(
          "absolute end-6 top-5 size-8 transition-colors duration-300 sm:end-5",
          lit ? "text-primary" : "text-muted-foreground"
        )}
      />
      <span className="font-heading text-xl font-medium lowercase">
        <KeepAcronyms text={title} />
        <span className="blue-dot">.</span>
      </span>
      <span className="text-sm leading-snug text-muted-foreground">
        {children}
      </span>
    </li>
  )
}
