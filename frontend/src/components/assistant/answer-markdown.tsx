"use client"

import Markdown from "react-markdown"

import { LocalizedLink } from "@/components/common/localized-link"
import { MarkdownCode } from "@/components/common/markdown-code"
import { ANSWER_MARKDOWN } from "@/lib/markdown"

/** An assistant's answer: its limited markdown (lib/markdown.ts), links to the app's own pages
 * only; `onNavigate` runs when one is followed. */
export function AnswerMarkdown({
  text,
  onNavigate,
}: {
  text: string
  onNavigate: () => void
}) {
  return (
    <div className="space-y-2 [&_ol]:list-decimal [&_ol]:ps-5 [&_ul]:list-disc [&_ul]:ps-5">
      <Markdown
        {...ANSWER_MARKDOWN}
        components={{
          pre: ({ children }) => <MarkdownCode>{children}</MarkdownCode>,
          a: ({ href, children }) =>
            href ? (
              <LocalizedLink
                href={href}
                onClick={onNavigate}
                className="underline underline-offset-4"
              >
                {children}
              </LocalizedLink>
            ) : (
              <span>{children}</span>
            ),
        }}
      >
        {text}
      </Markdown>
    </div>
  )
}
