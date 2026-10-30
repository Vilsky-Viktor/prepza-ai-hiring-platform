import { describe, expect, it } from "vitest"

import { noteAuthorName } from "@/lib/interview-notes"

const labels = { former: "Former member", deletedKey: "Deleted API key" }
const member = { former: false, api_key: false }
const key = { former: false, api_key: true }

describe("noteAuthorName", () => {
  it("names a member or an API key by their name", () => {
    expect(noteAuthorName({ ...member, name: "Ann" }, labels)).toBe("Ann")
    expect(noteAuthorName({ ...key, name: "Careers site" }, labels)).toBe(
      "Careers site"
    )
  })

  it("names a former member and a deleted key by what they are", () => {
    expect(noteAuthorName({ ...member, former: true }, labels)).toBe(
      labels.former
    )
    expect(noteAuthorName({ ...key, name: null }, labels)).toBe(
      labels.deletedKey
    )
  })

  it("names no one for a member without a name", () => {
    expect(noteAuthorName({ ...member, name: null }, labels)).toBeNull()
  })
})
