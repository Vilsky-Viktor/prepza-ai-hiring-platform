import { readFileSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import en from "@/messages/en.json"

import { SOURCE_ROOT, sourceFiles } from "../source-files"

// A message with a tag (<bdi>, <b>, <link>) only shows through t.rich or t.markup; plain t()
// throws "didn't resolve to a string" and the page shows the key instead. This finds plain t()
// calls, by the namespace their t was made for, whose English message has a tag.

const SOURCES = ["app", "components", "features", "hooks", "lib"]
const TAG = /<\w+>/

function message(key: string): unknown {
  return key.split(".").reduce<unknown>(
    (node, part) => (node && typeof node === "object" ? (node as Record<string, unknown>)[part] : undefined),
    en
  )
}

// Each translator a file makes: its variable and namespace.
function translators(source: string) {
  const found: [string, string][] = []

  for (const match of source.matchAll(
    /const (\w+) = (?:await )?(?:useTranslations|getTranslations)\(\s*(?:"([\w.]+)"|\{[^}]*namespace:\s*"([\w.]+)"[^}]*\})\s*\)/g
  )) {
    found.push([match[1], match[2] ?? match[3]])
  }

  return found
}

function plainCallsWithTags(file: string) {
  const source = readFileSync(file, "utf8")
  const offenders: string[] = []

  for (const [name, namespace] of translators(source)) {
    // name("key"... or name(cond ? "a" : "b"..., but not name.rich / name.markup / name.raw.
    const call = new RegExp(`(?<![\\w.])${name}\\(([^()]*?)(?:,|\\))`, "g")

    for (const match of source.matchAll(call)) {
      for (const key of match[1].matchAll(/"([\w.]+)"/g)) {
        const text = message(`${namespace}.${key[1]}`)

        if (typeof text === "string" && TAG.test(text)) {
          offenders.push(`${path.relative(SOURCE_ROOT, file)}: ${name}("${key[1]}") (${namespace})`)
        }
      }
    }
  }

  return offenders
}

describe("messages with tags", () => {
  it("are only shown through t.rich or t.markup", () => {
    const offenders = sourceFiles(SOURCES, /\.tsx?$/).flatMap(plainCallsWithTags)

    expect(offenders).toEqual([])
  })
})
