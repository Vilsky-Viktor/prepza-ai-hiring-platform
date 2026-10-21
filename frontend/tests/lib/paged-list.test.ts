import { describe, expect, it } from "vitest"

import { PAGE_SIZE } from "@/constants/lists"
import { byId, mergePages, nextPagePath, pagePath } from "@/lib/paged-list"

describe("pagePath", () => {
  it("starts the query when the path has none", () => {
    expect(pagePath("/companies/companies", 40)).toBe(
      `/companies/companies?offset=40&limit=${PAGE_SIZE}`
    )
  })

  it("adds to a query the path already has", () => {
    expect(pagePath("/x?sort=finished", 0)).toBe(
      `/x?sort=finished&offset=0&limit=${PAGE_SIZE}`
    )
  })
})

describe("mergePages", () => {
  it("leaves out rows the first pages already have, keeping the order", () => {
    const first = [{ id: "a" }, { id: "b" }]
    const rest = [{ id: "b" }, { id: "c" }, { id: "a" }, { id: "d" }]

    expect(mergePages(first, rest, byId).map(byId)).toEqual([
      "a",
      "b",
      "c",
      "d",
    ])
  })

  it("keeps the first rows' own objects", () => {
    const first = [{ id: "a", title: "old" }]
    const merged = mergePages(first, [{ id: "a", title: "new" }], byId)

    expect(merged).toEqual([{ id: "a", title: "old" }])
  })

  it("works with any key and empty pages", () => {
    const key = (item: string) => item.toLowerCase()

    expect(mergePages(["A"], ["a", "B"], key)).toEqual(["A", "B"])
    expect(mergePages([], ["x"], key)).toEqual(["x"])
    expect(mergePages(["x"], [], key)).toEqual(["x"])
  })
})

describe("nextPagePath", () => {
  const rows = [{ id: "a" }, { id: "b/c" }]

  it("asks for the next page by offset", () => {
    expect(nextPagePath("/x", rows, byId, false)).toBe(
      `/x?offset=2&limit=${PAGE_SIZE}`
    )
  })

  it("asks for the page after the last row's key for a list paged by key", () => {
    expect(nextPagePath("/x", rows, byId, true)).toBe(
      `/x?offset=2&limit=${PAGE_SIZE}&after=b%2Fc`
    )
  })
})
