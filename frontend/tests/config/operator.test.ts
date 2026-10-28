import { readFileSync } from "node:fs"

import { describe, expect, it } from "vitest"

import { OPERATOR, OPERATOR_POSTAL_ADDRESS } from "@/config/operator"

// The legal texts and the emails take the operator from the shared Python constants; the site's
// footer, contact page and structured data from this mirror. They must say the same.
const SHARED = readFileSync(
  new URL(
    "../../../packages/common/src/prepza_common/config/constants.py",
    import.meta.url
  ),
  "utf8"
)

function shared(key: string) {
  return new RegExp(`"${key}": "([^"]+)"`).exec(SHARED)?.[1]
}

describe("OPERATOR", () => {
  it("matches the shared constants the legal texts and emails use", () => {
    expect(OPERATOR).toEqual({
      name: shared("name"),
      registryCode: shared("registry_code"),
      address: shared("address"),
      email: shared("email"),
    })
  })

  it("has the same address in its parts as in one line", () => {
    const parts = OPERATOR_POSTAL_ADDRESS

    expect(OPERATOR.address).toBe(
      `${parts.streetAddress}, ${parts.postalCode} ${parts.addressLocality}, ${parts.addressRegion}, Estonia`
    )
    expect(parts.addressCountry).toBe("EE")
  })
})
