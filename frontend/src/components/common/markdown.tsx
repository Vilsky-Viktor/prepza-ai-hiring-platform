import { cn } from "cn"
import type { ComponentProps, ReactNode } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { LocalizedLink } from "@/components/common/localized-link"
import { HighlightedCode } from "@/components/common/highlighted-code"
import { markdownCode } from "@/components/common/markdown-code"
import { TEXT_LINK } from "@/config/links"
import { endsWithQuestionMark } from "@/lib/question-mark"

/** A link in the site's text: the site's own pages open in place, in the address's language;
 * others in a new tab; styled as an in-text link (config/links.ts). */
export function SiteLink({
  href = "",
  children,
}: {
  href?: string
  children?: ReactNode
}) {
  return href.startsWith("/") ? (
    <LocalizedLink href={href} className={TEXT_LINK}>
      {children}
    </LocalizedLink>
  ) : (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={TEXT_LINK}
    >
      {children}
    </a>
  )
}

// The site's text styles for each Markdown element, as on the legal pages. Headings keep their
// capitals (names such as TestGorilla or EU), unlike the site's lowercase headings.
const ELEMENTS: ComponentProps<typeof ReactMarkdown>["components"] = {
  // A question gets no dot after its question mark (globals.css).
  h2: ({ children }) => (
    <h2
      className={cn(
        "pt-4 font-heading text-2xl font-medium normal-case",
        endsWithQuestionMark(String(children)) && "no-dot"
      )}
    >
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-xl font-medium normal-case">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="text-base leading-relaxed text-muted-foreground">
      {children}
    </p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc space-y-2 ps-5 text-base leading-relaxed text-muted-foreground">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal space-y-2 ps-5 text-base leading-relaxed text-muted-foreground">
      {children}
    </ol>
  ),
  strong: ({ children }) => (
    <strong className="font-medium text-foreground">{children}</strong>
  ),
  a: SiteLink,
  // Colored on the server, so an article doesn't load shiki.
  pre: ({ children }) => {
    const block = markdownCode(children)

    return block ? (
      <HighlightedCode {...block} className="my-2" />
    ) : (
      <pre>{children}</pre>
    )
  },
  table: ({ children }) => (
    <div className="overflow-x-auto rounded-xl border">
      {/* A body row lights up on hover in the search field's grey, as ROW_HOVER (config/lists.ts)
          colours the site's list rows, so the eye follows it. */}
      <table className="w-full text-sm [&_tbody_tr]:transition-colors [&_tbody_tr:hover]:bg-surface">
        {children}
      </table>
    </div>
  ),
  th: ({ children }) => (
    <th className="px-4 py-3 text-start font-medium">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border-t px-4 py-3 align-top text-muted-foreground">
      {children}
    </td>
  ),
}

/** Markdown from the site's own content files, with tables. */
export function Markdown({ text }: { text: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={ELEMENTS}>
      {text}
    </ReactMarkdown>
  )
}
