import { cn } from "cn"
import type { LucideIcon } from "lucide-react"

import { KeepAcronyms } from "@/components/common/keep-acronyms"

/** A grey landing card: a title ending with the logo's blue dot, a short line and its icon in
 * the top corner; ringed, with its icon blue, while `lit`. */
export function IconCard({
  icon: Icon,
  title,
  lit = false,
  children,
}: {
  icon: LucideIcon
  title: string
  lit?: boolean
  children: React.ReactNode
}) {
  return (
    <li
      data-testid="icon-card"
      data-lit={lit || undefined}
      className={cn(
        "relative flex flex-col justify-center gap-1.5 rounded-xl bg-surface p-4 pe-14 transition-shadow duration-300 sm:p-5 sm:pe-16",
        lit && "border-primary-gradient"
      )}
    >
      <Icon
        className={cn(
          "absolute end-4 top-4 size-8 transition-colors duration-300 sm:end-5 sm:top-5",
          lit ? "text-primary" : "text-muted-foreground"
        )}
      />
      <span className="font-heading text-xl font-medium lowercase">
        <KeepAcronyms text={title} />
        <span className="text-primary">.</span>
      </span>
      <span className="text-sm leading-snug text-muted-foreground">
        {children}
      </span>
    </li>
  )
}
