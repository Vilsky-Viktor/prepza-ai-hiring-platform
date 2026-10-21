import { cn } from "cn"
import { ArrowRightIcon } from "lucide-react"

import { KeepAcronyms } from "@/components/keep-acronyms"
import { LocalizedLink } from "@/components/localized-link"
import { buttonVariants } from "@/components/ui/button"
import { endsWithQuestionMark } from "@/lib/question-mark"

/** One landing section, a screen of its own: a large title and a short text, centered, and
 * its picture below. */
export function LandingSection({
  id,
  title,
  text,
  extra,
  children,
}: {
  id?: string
  title: string
  // Usually plain text; a section may end it with a link.
  text: React.ReactNode
  extra?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <section
      id={id}
      className="flex min-h-[calc(100svh-3.5rem)] scroll-mt-14 flex-col justify-center gap-14 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-3xl space-y-4 text-center">
        {/* A title over two lines ends each with the logo's blue dot, like the hero's. */}
        <h2
          className={cn(
            "font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl",
            (title.includes("\n") || endsWithQuestionMark(title)) && "no-dot"
          )}
        >
          {title.includes("\n") ? (
            title.split("\n").map((line) => (
              <span key={line} className="block">
                <KeepAcronyms text={line} />
                <span className="text-primary">.</span>
              </span>
            ))
          ) : (
            <KeepAcronyms text={title} />
          )}
        </h2>
        <p className="mx-auto max-w-2xl text-lg leading-relaxed text-balance text-muted-foreground sm:text-xl">
          {text}
        </p>
        {extra}
      </div>
      {children}
    </section>
  )
}

/** The landing's outline button: the demos', the video's and a section's link onwards. */
export const OUTLINE_BUTTON =
  "gap-2 border-foreground/20 text-base dark:border-input"

/** A link onwards from a section, as an outline button; its arrow faces the reading direction. */
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
      <ArrowRightIcon className="size-4 rtl:-scale-x-100" />
    </LocalizedLink>
  )
}
