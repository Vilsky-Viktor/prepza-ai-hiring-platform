import { readdirSync, readFileSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import en from "@/messages/en.json"

// A date inside a sentence is a <time> tag around its value, so the page shows it in a <time>
// element (in italics). Every language keeps the tag around the same value as English.

const DIR = path.resolve(__dirname, "../../messages")
const TIME = /<time>(\{\w+\})<\/time>/

type Messages = { [key: string]: string | Messages }

function strings(messages: Messages, prefix = ""): [string, string][] {
  return Object.entries(messages).flatMap(([key, value]) => {
    const name = prefix ? `${prefix}.${key}` : key

    return typeof value === "string" ? [[name, value]] : strings(value, name)
  })
}

function at(messages: Messages, key: string) {
  return key
    .split(".")
    .reduce<string | Messages | undefined>(
      (node, part) =>
        node && typeof node === "object" ? node[part] : undefined,
      messages
    )
}

const dated = strings(en as Messages).filter(([, text]) => TIME.test(text))

describe("dates in messages", () => {
  it("are tagged in English", () => {
    expect(dated.length).toBeGreaterThan(0)
  })

  for (const file of readdirSync(DIR).filter((name) =>
    name.endsWith(".json")
  )) {
    it(`keep their <time> tag in ${file}`, () => {
      const messages = JSON.parse(
        readFileSync(path.join(DIR, file), "utf8")
      ) as Messages
      const wrong = dated.filter(([key, text]) => {
        const value = at(messages, key)

        return (
          typeof value !== "string" ||
          value.match(/<time>/g)?.length !== 1 ||
          !value.includes(`<time>${text.match(TIME)?.[1]}</time>`)
        )
      })

      expect(wrong.map(([key]) => key)).toEqual([])
    })
  }
})
