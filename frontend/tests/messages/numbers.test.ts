import { readFileSync, readdirSync } from "node:fs"
import path from "node:path"
import {
  type MessageFormatElement,
  parse,
  TYPE,
} from "@formatjs/icu-messageformat-parser"
import { createTranslator } from "next-intl"
import { describe, expect, it } from "vitest"

import { bdiText } from "@/lib/bidi"
import de from "../../messages/de.json"
import en from "../../messages/en.json"
import ru from "../../messages/ru.json"

const DIR = path.resolve(__dirname, "../../messages")
const CODES = readdirSync(DIR).map((name) => name.replace(".json", ""))

// Arguments that always hold a count or an amount: in English each is a plural or a formatted
// number, never bare, so every language can pick its form and write the number its way.
const NUMBER_ARGS = [
  "available",
  "copies",
  "count",
  "credits",
  "days",
  "fast",
  "kb",
  "leaves",
  "max",
  "minutes",
  "number",
  "passed",
  "points",
  "practice",
  "ready",
  "reserved",
  "right",
  "sections",
  "threshold",
  "total",
]
// French, Spanish, Italian and Portuguese use `many` only for compact millions.
const OPTIONAL: Record<string, string[]> = {
  fr: ["many"],
  es: ["many"],
  it: ["many"],
  pt: ["many"],
}
// An exact value covers its category.
const EXACT: Record<string, string> = { zero: "=0", one: "=1", two: "=2" }

type Messages = { [key: string]: string | string[] | Messages }

function load(code: string): Messages {
  return JSON.parse(readFileSync(path.join(DIR, `${code}.json`), "utf8"))
}

function flat(value: Messages, prefix = ""): [string, string][] {
  return Object.entries(value).flatMap(([key, item]) => {
    const name = prefix ? `${prefix}.${key}` : key

    if (typeof item === "string") {
      return [[name, item]]
    }

    return Array.isArray(item) ? [] : flat(item, name)
  })
}

// Every element of a message, nested ones too.
function walk(elements: MessageFormatElement[]): MessageFormatElement[] {
  return elements.flatMap((element) => {
    if (element.type === TYPE.plural || element.type === TYPE.select) {
      return [
        element,
        ...Object.values(element.options).flatMap((option) =>
          walk(option.value)
        ),
      ]
    }

    return element.type === TYPE.tag
      ? [element, ...walk(element.children)]
      : [element]
  })
}

// The plurals of one language's messages that leave out a category it has.
function missingCategories(code: string) {
  const needed = new Intl.PluralRules(code)
    .resolvedOptions()
    .pluralCategories.filter(
      (category) => !(OPTIONAL[code] ?? []).includes(category)
    )

  return flat(load(code)).flatMap(([key, text]) =>
    walk(parse(text, { ignoreTag: false })).flatMap((element) => {
      if (element.type !== TYPE.plural) {
        return []
      }

      const missing = needed.filter(
        (category) =>
          !element.options[category] && !element.options[EXACT[category]]
      )

      return missing.length
        ? [`${code} ${key} ${element.value}: ${missing.join(", ")}`]
        : []
    })
  )
}

describe("plural categories", () => {
  it.each(CODES)("%s fills every category its language has", (code) => {
    expect(missingCategories(code)).toEqual([])
  })
})

describe("numbers in English messages", () => {
  it("are never a bare argument", () => {
    const bare = flat(load("en")).flatMap(([key, text]) =>
      walk(parse(text, { ignoreTag: false }))
        .filter(
          (element) =>
            element.type === TYPE.argument &&
            NUMBER_ARGS.includes(element.value)
        )
        .map((element) => `${key}: {${"value" in element && element.value}}`)
    )

    expect(bare).toEqual([])
  })
})

describe("plural forms", () => {
  it("pick the noun's form by the number", () => {
    const t = createTranslator({ locale: "ru", messages: ru })

    expect(t("autoTopUp.level", { threshold: 1 })).toBe("1 кредит")
    expect(t("autoTopUp.level", { threshold: 3 })).toBe("3 кредита")
    expect(t("autoTopUp.level", { threshold: 25 })).toBe("25 кредитов")
  })

  it("write the number as the language does", () => {
    const german = createTranslator({ locale: "de", messages: de })
    const english = createTranslator({ locale: "en", messages: en })
    const adjust = (amount: number) =>
      english.markup("superadmin.adjustConfirmTitle", {
        amount,
        name: "Acme",
        ...bdiText,
      })

    expect(german("billing.currentBalance", { amount: 1500 })).toContain(
      "1.500"
    )
    expect(adjust(5)).toMatch(/^\+5 /)
    expect(adjust(-5)).toMatch(/^-5 /)
  })
})
