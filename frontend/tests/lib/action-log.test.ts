import { describe, expect, it } from "vitest"

import { actionFilters } from "@/lib/action-log"

describe("actionFilters", () => {
  it("keeps the log's filters the address gives, without empty ones or others", () => {
    const filters = actionFilters({
      member_id: "m-1",
      group: "",
      from: "2026-10-01",
      page: "2",
    })

    expect(filters.toString()).toBe("member_id=m-1&from=2026-10-01")
  })
})
