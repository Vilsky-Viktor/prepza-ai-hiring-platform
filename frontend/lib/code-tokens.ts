import { CODE_THEMES } from "@/constants/code"
import { splitCodeBlocks } from "@/lib/question-text"

export type CodeToken = { content: string; style?: Record<string, string> }

/** Code as the editor shows it: a file's last new line would show as an empty numbered line. */
export function editorText(code: string) {
  return code.replace(/\n+$/, "")
}

/** The code's lines as colored tokens in both themes (shiki, loaded on first use); null without
 * a language or for one shiki doesn't know, so the code shows plain. Runs on the server for
 * pages' own code (components/highlighted-code.tsx) and in the browser for code that arrives
 * there (hooks/use-highlight.ts). */
export async function codeTokens(
  code: string,
  language?: string
): Promise<CodeToken[][] | null> {
  if (!language) {
    return null
  }

  const { bundledLanguages, codeToTokens } = await import("shiki")

  if (!(language in bundledLanguages)) {
    return null
  }

  const { tokens } = await codeToTokens(code, {
    lang: language as keyof typeof bundledLanguages,
    themes: CODE_THEMES,
    defaultColor: false,
  })

  return tokens.map((line) =>
    line.map((token) => ({
      content: token.content,
      style: token.htmlStyle as Record<string, string> | undefined,
    }))
  )
}

/** The colors of a question's code blocks, in order, for a server page's QuestionText
 * (`codeColors`). */
export function questionCodeColors(text: string) {
  return Promise.all(
    splitCodeBlocks(text)
      .filter((part) => part.code)
      .map((part) => codeTokens(editorText(part.text), part.language))
  )
}
