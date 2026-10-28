import { statSync } from "node:fs"

import { describe, expect, it } from "vitest"

import { ATS_PROVIDERS } from "@/config/ats"

// The ATS logos show at most 48 px wide (24 px on the home page): small files, never photos.
const MAX_BYTES = 20_000

describe("the ATS logos", () => {
  it("stay small files", () => {
    for (const provider of ATS_PROVIDERS) {
      for (const file of [provider.logo, provider.wordmark]) {
        const size = statSync(
          new URL(`../../public${file}`, import.meta.url)
        ).size

        expect(size, file).toBeLessThanOrEqual(MAX_BYTES)
      }
    }
  })
})
