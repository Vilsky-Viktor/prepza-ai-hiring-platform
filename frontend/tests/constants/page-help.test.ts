import { existsSync, readdirSync, readFileSync } from "node:fs"
import { dirname, join, relative } from "node:path"
import { describe, expect, it } from "vitest"

import { COMPANY_INTERVIEW_PAGE, TIMED_PAGE } from "@/constants/layout"
import {
  COMPANY_TAB_HELP,
  INTERVIEW_TAB_HELP,
  PAGE_HELP_KEYS,
} from "@/constants/page-help"

import { FRONTEND, SOURCE_ROOT } from "../source-files"

// The page code's paths are relative to SOURCE_ROOT; messages/ and the repo's other files to
// the frontend's folder.
const read = (path: string) => readFileSync(join(FRONTEND, path), "utf8")
const readSource = (path: string) =>
  readFileSync(join(SOURCE_ROOT, path), "utf8")
const locales = readdirSync(join(FRONTEND, "messages")).map((name) =>
  name.replace(".json", "")
)

// What registers a page's key for the assistant, and the shared component that does it for the
// pages using it (each of which must register itself).
const REGISTERS: [RegExp, string][] = [
  [/<PageHelp\b/, "components/page-help.tsx"],
  [/<PageKey\b/, "components/page-key.tsx"],
  [/\bhelp=/, "components/back-link.tsx"],
  [/<CompanyHeader\b/, "components/company/company-header.tsx"],
  [/<InterviewHeader\b/, "components/company/interview-header.tsx"],
  [/<LegalPage\b/, "components/legal-page.tsx"],
  [
    /\b(categoryRoute|hubArticleRoute)\(/,
    "components/content/content-article.tsx",
  ],
  [/<GenerationView\b/, "components/generation/generation-view.tsx"],
  [/<GenerationProgress\b/, "components/generation/generation-progress.tsx"],
]

// A page that is not found outside development.
const DEVELOPMENT_ONLY =
  /if \(process\.env\.NODE_ENV !== "development"\) \{\s*notFound\(\)/

/** Every page file under app/, as its route ("/companies/[companyId]/billing"). */
function pages(dir = "app"): string[] {
  return readdirSync(join(SOURCE_ROOT, dir), { withFileTypes: true }).flatMap(
    (entry) => {
      const path = join(dir, entry.name)

      if (entry.isDirectory()) {
        return pages(path)
      }

      return entry.name === "page.tsx" ? [path] : []
    }
  )
}

/** The page's file and the layouts above it, which may register for it. */
function sources(page: string) {
  const files = [page]

  for (let dir = dirname(page); dir !== "."; dir = dirname(dir)) {
    const layout = join(dir, "layout.tsx")

    if (existsSync(join(SOURCE_ROOT, layout))) {
      files.push(layout)
    }
  }

  return files.map(readSource).join("\n")
}

describe("page help", () => {
  it("gives every company and interview tab its own page's text", () => {
    const tabs = [
      ...Object.values(COMPANY_TAB_HELP),
      ...Object.values(INTERVIEW_TAB_HELP),
    ]

    expect(new Set(tabs).size).toBe(tabs.length)

    for (const key of tabs) {
      expect(PAGE_HELP_KEYS).toContain(key)
    }

    expect(COMPANY_TAB_HELP.members).toBe("team")
  })

  it("has the keys rounds serves guides for", () => {
    const python = read("../packages/common/src/prepza_common/page_keys.py")
    const keys = [...python.matchAll(/^\s+"(\w+)",$/gm)].map(
      (match) => match[1]
    )

    expect([...PAGE_HELP_KEYS]).toEqual(keys)
  })

  it.each(locales)("keeps no guide text of its own in %s", (code) => {
    const help = JSON.parse(read(`messages/${code}.json`)).pageHelp

    expect(Object.keys(help).sort()).toEqual([
      "actionsTitle",
      "label",
      "tipsTitle",
    ])
  })

  it("registers a key on every page where the assistant's panel opens", () => {
    for (const [, component] of REGISTERS) {
      expect(readSource(component), component).toMatch(
        /usePageKey\(|<PageHelp\b|<PageKey\b|\bhelp=/
      )
    }

    expect(pages().length).toBeGreaterThan(0)

    const missing = pages().filter((page) => {
      const route =
        "/" + relative("app", dirname(page)).replace(/\[[^\]]+\]/g, "x")
      const source = sources(page)
      // The admin zone, pages without the header (and so without the panel), the maintenance
      // page shown in place of any page, pages that only redirect, and development-only pages
      // (not found anywhere else, so no visitor opens the panel there).
      const exempt =
        route.startsWith("/superadmin") ||
        TIMED_PAGE.test(route + "/") ||
        COMPANY_INTERVIEW_PAGE.test(route + "/") ||
        COMPANY_INTERVIEW_PAGE.test(route) ||
        route === "/maintenance" ||
        /\bredirect\(/.test(readSource(page)) ||
        DEVELOPMENT_ONLY.test(readSource(page))

      return !exempt && !REGISTERS.some(([marker]) => marker.test(source))
    })

    expect(missing).toEqual([])
  })
})
