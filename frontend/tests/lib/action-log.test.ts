import { describe, expect, it } from "vitest"

import { actionAuthor, actionFilters } from "@/lib/action-log"

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

describe("actionAuthor", () => {
  const action = { key_id: null, key_name: null, user_email: null, via: null }

  it("names a member by email, and one who's gone as a former member", () => {
    expect(actionAuthor({ ...action, user_email: "ann@example.com" })).toEqual({
      kind: "member",
      email: "ann@example.com",
    })
    expect(actionAuthor(action)).toEqual({ kind: "former" })
  })

  it("names an API key by its name with the way it came, the API by default", () => {
    const key = { ...action, key_id: "k-1", key_name: "Careers site" }

    expect(actionAuthor({ ...key, via: "mcp" })).toEqual({
      kind: "key",
      name: "Careers site",
      via: "mcp",
    })
    expect(actionAuthor(key)).toEqual({
      kind: "key",
      name: "Careers site",
      via: "api",
    })
  })

  it("names a deleted key by the way it came, not its maker", () => {
    expect(
      actionAuthor({
        ...action,
        key_id: "k-1",
        user_email: "ann@example.com",
        via: "mcp",
      })
    ).toEqual({ kind: "deletedKey", via: "mcp" })
  })
})
