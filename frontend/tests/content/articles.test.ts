import { readdirSync, readFileSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import { LOCALES } from "@/constants/i18n"

// The articles' rules (.claude/rules/content-i18n.md): front matter, the body's first heading,
// slugs, and one translation per language that keeps the original's sections and links.
const ROOT = path.resolve(__dirname, "../../content")
const FOLDERS = ["guides", "compare", "pages"]
const SEO_TITLE_MAX = 60
const DESCRIPTION_MAX = 155

type Article = { file: string; meta: Record<string, string>; body: string }

function read(file: string): Article {
  const text = readFileSync(path.join(ROOT, file), "utf8")
  const [, head = "", body = text] =
    text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/) ?? []
  const meta = Object.fromEntries(
    head.split("\n").map((line) => {
      const at = line.indexOf(":")

      return [
        line.slice(0, at).trim(),
        line
          .slice(at + 1)
          .trim()
          .replace(/^"|"$/g, ""),
      ]
    })
  )

  return { file, meta, body }
}

function articles(folder: string, locale = "en") {
  const dir = locale === "en" ? folder : path.join(locale, folder)

  return readdirSync(path.join(ROOT, dir))
    .filter((name) => name.endsWith(".md"))
    .map((name) => read(path.join(dir, name)))
}

const translations = LOCALES.filter((locale) => locale !== "en")
const sections = (body: string) => body.match(/^##+ /gm)?.length ?? 0
const links = (body: string) =>
  [...body.matchAll(/\]\(([^)]+)\)/g)].map(([, link]) => link).sort()

describe.each(FOLDERS)("the %s articles", (folder) => {
  const originals = articles(folder)
  const all = [
    ...originals,
    ...translations.flatMap((locale) => articles(folder, locale)),
  ]

  it("have their front matter within its limits", () => {
    const wrong = all.flatMap(({ file, meta }) => [
      ...["title", "seoTitle", "description", "updated"]
        .filter((key) => !meta[key])
        .map((key) => `${file}: no ${key}`),
      ...((meta.seoTitle ?? "").length > SEO_TITLE_MAX
        ? [`${file}: seoTitle too long`]
        : []),
      ...((meta.description ?? "").length > DESCRIPTION_MAX
        ? [`${file}: description too long`]
        : []),
      ...(/^\d{4}-\d{2}-\d{2}$/.test(meta.updated ?? "")
        ? []
        : [`${file}: updated isn't YYYY-MM-DD`]),
    ])

    expect(wrong).toEqual([])
  })

  it("start their body with the title and have lowercase hyphenated slugs", () => {
    const wrong = all.filter(
      ({ file, meta, body }) =>
        body.trimStart().split("\n")[0] !== `# ${meta.title}` ||
        !/^[a-z0-9]+(-[a-z0-9]+)*\.md$/.test(path.basename(file))
    )

    expect(wrong.map(({ file }) => file)).toEqual([])
  })

  it("have one translation per language, with the original's sections and links", () => {
    const wrong = translations.flatMap((locale) => {
      const translated = new Map(
        articles(folder, locale).map((item) => [path.basename(item.file), item])
      )

      return originals.flatMap((original) => {
        const name = path.basename(original.file)
        const item = translated.get(name)

        if (!item) {
          return [`${locale}/${folder}/${name}: missing`]
        }

        return sections(item.body) !== sections(original.body) ||
          links(item.body).join() !== links(original.body).join()
          ? [`${item.file}: sections or links differ`]
          : []
      })
    })

    expect(wrong).toEqual([])
  })
})
