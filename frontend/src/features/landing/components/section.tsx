import { cn } from "cn"

import { KeepAcronyms } from "@/components/common/keep-acronyms"
import { endsWithQuestionMark } from "@/lib/question-mark"

/** One landing section, a screen of its own: a large title and a short text, centered, and
 * its picture below. */
export function LandingSection({
  id,
  title,
  text,
  extra,
  background,
  children,
}: {
  id?: string
  title: string
  // Usually plain text; a section may end it with a link.
  text: React.ReactNode
  extra?: React.ReactNode
  // Its background across the window, top to bottom (config/landing-backgrounds.ts).
  background?: string
  children?: React.ReactNode
}) {
  return (
    <section
      id={id}
      className={cn(
        "flex min-h-[calc(100svh-3.5rem)] scroll-mt-14 flex-col justify-center gap-14 py-20 sm:py-28",
        background
      )}
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
                <span className="blue-dot">.</span>
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
