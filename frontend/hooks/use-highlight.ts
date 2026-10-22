"use client"

import { useEffect, useState } from "react"

import { type CodeToken, codeTokens } from "@/lib/code-tokens"

/** The code's lines as colored tokens, once shiki has loaded the language in the browser; null
 * until then, without a language, or for one it doesn't know, so the code shows plain meanwhile.
 * For code that arrives in the browser; a page's own code comes colored from the server. */
export function useHighlight(code: string, language?: string) {
  // The lines with the code and language they were made for, so a change shows plain at once.
  const [result, setResult] = useState<{
    code: string
    language: string
    lines: CodeToken[][]
  } | null>(null)

  useEffect(() => {
    let current = true

    if (!language) {
      return
    }

    void codeTokens(code, language).then((lines) => {
      if (current && lines) {
        setResult({ code, language, lines })
      }
    })

    return () => {
      current = false
    }
  }, [code, language])

  return result?.code === code && result.language === language
    ? result.lines
    : null
}
