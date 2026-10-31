import { cn } from "cn"

import { LocalizedLink } from "@/components/common/localized-link"
import { buttonVariants } from "@/components/ui/button"

/** The landing's outline button: the demos', the video's and a section's link onwards. */
export const OUTLINE_BUTTON =
  "gap-2 border-foreground/20 text-base dark:border-input"

/** A link onwards from a section, as an outline button: the landing's and the features page's
 * standard button. */
export function MoreLink({
  href,
  keepCase = false,
  className,
  children,
}: {
  href: string
  // For a label written in lowercase already, with an abbreviation to keep ("go to FAQ").
  keepCase?: boolean
  className?: string
  children: React.ReactNode
}) {
  return (
    <LocalizedLink
      href={href}
      className={cn(
        buttonVariants({ variant: "outline" }),
        OUTLINE_BUTTON,
        "h-11 px-6",
        keepCase ? "normal-case" : "lowercase",
        className
      )}
    >
      {children}
    </LocalizedLink>
  )
}
