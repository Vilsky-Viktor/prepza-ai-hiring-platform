import { cn } from "cn"

import { CodeEditor } from "@/components/common/code-editor"
import { InlineText } from "@/components/questions/inline-text"
import type { CodeToken } from "@/lib/code-tokens"
import { splitCodeBlocks } from "@/lib/question-text"

/** A question's text with its code blocks in the code editor. `codeColors`, its code blocks'
 * colors in order when a server page made them (questionCodeColors), spare the browser shiki. */
export function QuestionText({
  text,
  heading = false,
  className,
  codeColors,
}: {
  text: string
  heading?: boolean
  className?: string
  codeColors?: (CodeToken[][] | null)[]
}) {
  const parts = splitCodeBlocks(text)

  return (
    <div
      role={heading ? "heading" : undefined}
      aria-level={heading ? 1 : undefined}
      // A heading takes focus when its question opens, for keyboard and screen reader users.
      tabIndex={heading ? -1 : undefined}
      className={cn("space-y-3", heading && "outline-none", className)}
    >
      {parts.map((part, index) =>
        part.code ? (
          <CodeEditor
            key={index}
            code={part.text}
            language={part.language}
            tokens={
              codeColors && [
                codeColors[parts.slice(0, index).filter((p) => p.code).length],
              ]
            }
            header={false}
          />
        ) : (
          <p key={index} className="bidi-auto whitespace-pre-line">
            <InlineText text={part.text.trim()} />
          </p>
        )
      )}
    </div>
  )
}
