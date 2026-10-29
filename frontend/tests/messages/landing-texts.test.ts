import { readFileSync, readdirSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import { keptCaseParts } from "@/lib/keep-case"

const DIR = path.resolve(__dirname, "../../messages")
const CODES = readdirSync(DIR).map((name) => name.replace(".json", ""))

type Messages = {
  home: { text: string; price: string }
  landing: { askAgent: string }
  assistant: { emptyTitle: string; emptyTitleFaq: string }
}

function messages(code: string): Messages {
  return JSON.parse(readFileSync(path.join(DIR, `${code}.json`), "utf8"))
}

// Mira's name, in any form a Latin or Cyrillic language gives it ("Mirę", "Миру").
const NAME = /(?<![\p{L}\p{N}])(Mir\p{L}*|Мир\p{L}*|Мір\p{L}*)/gu

describe.each(CODES)("%s", (code) => {
  const { home, landing, assistant } = messages(code)

  // The hero's sentences each on a line of their own: the page puts each message in its own
  // line, so each is one line of text, and the price's holds the price (the browser checks the
  // lines in English and Arabic, landing hero.spec.ts).
  it("has the hero's two sentences, the second with the price", () => {
    expect(home.text.trim()).not.toBe("")
    expect(home.text).not.toContain("\n")
    expect(home.price).toContain("{price}")
  })

  // Titles and buttons are lowercase, but Mira's name keeps its capital wherever it's written
  // (lib/keep-case.ts; the browser checks English and Russian, assistant.spec.ts).
  it("keeps Mira's name as written in the buttons and the welcome", () => {
    for (const text of [
      landing.askAgent,
      assistant.emptyTitle,
      assistant.emptyTitleFaq,
    ]) {
      const kept = keptCaseParts(text).filter((_, index) => index % 2)

      for (const [name] of text.matchAll(NAME)) {
        expect(kept, text).toContain(name)
      }
    }
  })
})
