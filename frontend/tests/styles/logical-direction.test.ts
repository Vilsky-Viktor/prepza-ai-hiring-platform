import { readFileSync } from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

import { SOURCE_ROOT, sourceFiles as filesIn } from "../source-files"

// Pages mirror right to left (ar, he, fa) only if their spacing and placement are logical:
// ms-/me-/ps-/pe-/start-/end-/text-start, never ml-/mr-/pl-/pr-/left-/text-left
// (.claude/rules/nextjs.md, "Languages and direction").
const DIRS = ["app", "components", "features", "hooks", "lib"]

// A physical class: margin, padding, placement, alignment, a side's radius or border, or a slide.
const PHYSICAL =
  /^-?(?:m[lr]|p[lr]|left|right|rounded-[lr]|rounded-[tb][lr]|border-[lr]|scroll-[mp][lr])-.+$|^text-(?:left|right)$|^(?:slide-in-from|slide-out-to)-(?:left|right)(?:-.+)?$/
// Centring (left-1/2 with -translate-x-1/2), print layouts kept off screen, and Base UI's own
// physical sides (data-[side=left]) stay as they are.
const ALLOWED = /^(?:left|right)-1\/2$|^-left-\[\d+px\]$/
// Places measured in the page's own pixels, or drawn on both sides alike.
const ALLOWED_IN: Record<string, RegExp> = {
  // The demo pointer moves to measured positions (offsetLeft), from the top-left corner.
  "components/landing/demo-pointer.tsx": /^-?left-(?:0|4)$/,
  // One wire runs from each edge of the window.
  "components/landing/hero-wires.tsx": /^(?:left|right)-full$/,
}
// Inline styles placed from a physical side.
const PHYSICAL_STYLE =
  /style=\{\{[^}]*\b(?:left|right|marginLeft|marginRight|paddingLeft|paddingRight)\s*:/

function sourceFiles() {
  return filesIn(DIRS, /\.(tsx?|css)$/)
}

/** The classes in a file's string literals that place, pad or align by a physical side. */
function physicalClasses(file: string, text: string) {
  const strings = text.match(/"[^"\n]*"|'[^'\n]*'|`[^`]*`/g) ?? []

  return strings.flatMap((literal) => {
    const tokens = literal.slice(1, -1).split(/\s+/)
    // A slide in from one side is fine with its right-to-left counterpart beside it.
    const mirrored = tokens.some((token) => token.startsWith("rtl:"))

    return tokens.filter((token) => {
      const variants = token.split(":")
      const utility = variants.at(-1) ?? ""

      if (!PHYSICAL.test(utility) || ALLOWED.test(utility)) {
        return false
      }

      if (variants.some((variant) => /side=(?:left|right)/.test(variant))) {
        return false
      }

      if (utility.startsWith("slide-") && mirrored) {
        return false
      }

      return !ALLOWED_IN[file]?.test(utility)
    })
  })
}

describe("direction-neutral layout", () => {
  it("uses logical classes and inline styles everywhere", () => {
    const found = sourceFiles()
      .filter((file) => !file.endsWith(".css"))
      .flatMap((full) => {
        const file = path.relative(SOURCE_ROOT, full)
        const text = readFileSync(full, "utf8")
        const styles = PHYSICAL_STYLE.test(text) ? ["inline style"] : []

        return [...physicalClasses(file, text), ...styles].map(
          (item) => `${file}: ${item}`
        )
      })

    expect(found).toEqual([])
  })

  it("uses logical properties in the style sheets", () => {
    const found = sourceFiles()
      .filter((file) => file.endsWith(".css"))
      .flatMap((full) =>
        readFileSync(full, "utf8")
          .split("\n")
          .filter((line) =>
            /^\s*(?:(?:margin|padding|border)-(?:left|right)|left|right|text-align:\s*(?:left|right))\b/.test(
              line
            )
          )
          .map((line) => `${path.relative(SOURCE_ROOT, full)}: ${line.trim()}`)
      )

    expect(found).toEqual([])
  })

  it("finds a physical class and lets centring and mirrored slides be", () => {
    expect(
      physicalClasses("x.tsx", `"ml-1 pe-2 left-1/2 hover:pl-3 text-right"`)
    ).toEqual(["ml-1", "hover:pl-3", "text-right"])
    expect(
      physicalClasses(
        "x.tsx",
        `"slide-in-from-left-3 rtl:slide-in-from-right-3 data-[side=left]:slide-in-from-right-2"`
      )
    ).toEqual([])
  })
})
