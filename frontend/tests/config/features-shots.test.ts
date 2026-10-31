import { readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"

import { FEATURE_GROUPS } from "@/config/features-page"
import { FEATURE_SHOTS, FEATURE_SHOTS_PATH } from "@/config/features-shots"

import { FRONTEND } from "../source-files"

const FOLDER = join(FRONTEND, "public", FEATURE_SHOTS_PATH)

/** A WebP file's width and height, from its first chunk (lossy "VP8 ", or "VP8X"). */
function webpSize(file: string) {
  const data = readFileSync(join(FOLDER, file))
  const chunk = data.toString("ascii", 12, 16)

  if (chunk === "VP8X") {
    return {
      width: data.readUIntLE(24, 3) + 1,
      height: data.readUIntLE(27, 3) + 1,
    }
  }

  expect(chunk, file).toBe("VP8 ")

  return {
    width: data.readUInt16LE(26) & 0x3fff,
    height: data.readUInt16LE(28) & 0x3fff,
  }
}

describe("the features page's pictures", () => {
  it("has a light and a dark picture of each shot, as large as its config says", () => {
    for (const [name, size] of Object.entries(FEATURE_SHOTS)) {
      for (const scheme of ["light", "dark"]) {
        expect(webpSize(`${name}-${scheme}.webp`), name).toEqual(size)
      }
    }
  })

  it("keeps only the pictures its rows show", () => {
    const shown = FEATURE_GROUPS.flatMap((group) =>
      group.rows.map((row) => row.shot)
    )
    const files = readdirSync(FOLDER).map((file) =>
      file.replace(/-(light|dark)\.webp$/, "")
    )

    expect(new Set(shown)).toEqual(new Set(Object.keys(FEATURE_SHOTS)))
    expect(new Set(files)).toEqual(new Set(Object.keys(FEATURE_SHOTS)))
    expect(files).toHaveLength(Object.keys(FEATURE_SHOTS).length * 2)
  })
})
