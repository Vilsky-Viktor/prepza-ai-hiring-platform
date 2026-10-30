import { readdirSync, readFileSync } from "node:fs"
import path from "node:path"
import { createTranslator } from "next-intl"
import { describe, expect, it } from "vitest"

import { bdiText } from "@/lib/bidi"
import { isLocale } from "@/lib/locale"

const DIR = path.resolve(__dirname, "../../messages")
// Notifications that name an interview; the bell passes "none" when it has no title yet.
const KINDS = [
  "question_flagged",
  "question_fixed",
  "candidate_finished",
  "invite_undelivered",
  "interview_ready",
  "ats_not_invited",
  "note_added",
]
const VALUES = {
  topic: "SQL",
  email: "a@b.c",
  grade: "none",
  ats: "Greenhouse",
  reason: "credits",
  authors: "Ann Lee",
}

describe("a notification about an interview without a title", () => {
  for (const locale of readdirSync(DIR)
    .map((name) => name.replace(".json", ""))
    .filter(isLocale)) {
    const messages = JSON.parse(
      readFileSync(path.join(DIR, `${locale}.json`), "utf8")
    )
    const t = createTranslator({
      locale,
      messages,
      namespace: "notifications.kinds",
    })

    it(`names no title in ${locale}, and quotes one that's there`, () => {
      for (const kind of KINDS) {
        for (const count of [1, 2]) {
          const untitled = t.markup(kind, {
            ...VALUES,
            count,
            title: "none",
            ...bdiText,
          })
          const titled = t.markup(kind, {
            ...VALUES,
            count,
            title: "Backend",
            ...bdiText,
          })

          expect(untitled, `${kind} ${count}`).not.toMatch(/none|“”|«»|„“|「」/)
          expect(titled, `${kind} ${count}`).toContain("Backend")
        }
      }
    })

    it(`names the latest notes' authors in ${locale}`, () => {
      for (const count of [1, 3]) {
        const text = t.markup("note_added", {
          ...VALUES,
          count,
          title: "Backend",
          ...bdiText,
        })

        expect(text, `${count}`).toContain("Ann Lee")
      }
    })
  }
})
