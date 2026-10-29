import { describe, expect, it } from "vitest"

import { splitPhoneTabs } from "@/lib/phone-tabs"

const PAGES = ["a", "b", "c", "d", "e"].map((id) => ({ id }))

function ids(items: readonly { id: string }[]) {
  return items.map((item) => item.id)
}

describe("splitPhoneTabs", () => {
  it("shows the first two and puts the rest, in order, in the menu", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "b")

    expect(ids(shown)).toEqual(["a", "b"])
    expect(ids(rest)).toEqual(["c", "d", "e"])
  })

  it("moves an open page from the menu into the last place", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "e")

    expect(ids(shown)).toEqual(["a", "e"])
    expect(ids(rest)).toEqual(["b", "c", "d"])
  })

  it("leaves the menu empty when there are two pages or fewer", () => {
    const { shown, rest } = splitPhoneTabs(PAGES.slice(0, 2), "b")

    expect(ids(shown)).toEqual(["a", "b"])
    expect(rest).toEqual([])
  })

  it("shows the first two when no page is open", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "x")

    expect(ids(shown)).toEqual(["a", "b"])
    expect(ids(rest)).toEqual(["c", "d", "e"])
  })
})
