import { isValidElement, type ReactNode } from "react"

import { CodeEditor } from "@/components/common/code-editor"

/** A Markdown code block ("```python" … "```") as react-markdown's `pre` gets it, whose child is
 * the `code` with its language as a class: its code and language, or null for anything else. */
export function markdownCode(children?: ReactNode) {
  if (!isValidElement<{ className?: string; children?: ReactNode }>(children)) {
    return null
  }

  const { className = "", children: text } = children.props

  return {
    code: String(text ?? "").replace(/\n$/, ""),
    language: /language-(\S+)/.exec(className)?.[1],
  }
}

/** A Markdown code block in the code editor, colored in the browser (the assistant's answers);
 * the site's own Markdown colors it on the server (components/common/markdown.tsx). */
export function MarkdownCode({ children }: { children?: ReactNode }) {
  const block = markdownCode(children)

  return block ? (
    <CodeEditor {...block} className="my-2" />
  ) : (
    <pre>{children}</pre>
  )
}
