import type { ComponentProps } from "react"

import { CodeEditor } from "@/components/common/code-editor"
import { codeTokens, editorText } from "@/lib/code-tokens"

/** The code editor for a page's own code (articles, the API docs, the home page's demo), colored
 * on the server, so the browser never loads shiki for it. */
export async function HighlightedCode(
  props: Omit<ComponentProps<typeof CodeEditor>, "tokens">
) {
  const options = props.variants ?? [
    { code: props.code ?? "", language: props.language },
  ]
  const tokens = await Promise.all(
    options.map((option) =>
      codeTokens(editorText(option.code), option.language)
    )
  )

  return <CodeEditor {...props} tokens={tokens} />
}
