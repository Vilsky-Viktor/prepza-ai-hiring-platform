"use client"

import { useState } from "react"

import { readChat, saveChat } from "@/lib/assistant-storage"

/** The company picked in the assistant's panel: by default the company of the page (null: all
 * companies outside a company's pages); a pick holds on the page it was made on, and is kept
 * with the restored chat. `known` are the user's companies: a pick that isn't one of them
 * (another account's) doesn't count. */
export function useCompanyChoice(page: string | null, known: string[]) {
  const [choice, setChoice] = useState(() => readChat(true).choice ?? null)
  const valid =
    choice !== null &&
    choice.page === page &&
    (choice.company === null || known.includes(choice.company))

  function pick(company: string | null) {
    const next = { page, company }
    setChoice(next)
    saveChat(true, { choice: next })
  }

  return { company: valid ? choice.company : page, pick }
}
