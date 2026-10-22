import { describe, expect, it } from "vitest"

import { splitPhoneTabs } from "@/lib/phone-tabs"

const PAGES = ["a", "b", "c", "d", "e"].map((id) => ({ id }))

function ids(items: readonly { id: string }[]) {
  return items.map((item) => item.id)
}

describe("splitPhoneTabs", () => {
  it("shows the first three and puts the rest, in order, in the menu", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "b")

    expect(ids(shown)).toEqual(["a", "b", "c"])
    expect(ids(rest)).toEqual(["d", "e"])
  })

  it("moves an open page from the menu into the third place", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "e")

    expect(ids(shown)).toEqual(["a", "b", "e"])
    expect(ids(rest)).toEqual(["c", "d"])
  })

  it("leaves the menu empty when there are three pages or fewer", () => {
    const { shown, rest } = splitPhoneTabs(PAGES.slice(0, 3), "c")

    expect(ids(shown)).toEqual(["a", "b", "c"])
    expect(rest).toEqual([])
  })

  it("shows the first three when no page is open", () => {
    const { shown, rest } = splitPhoneTabs(PAGES, "x")

    expect(ids(shown)).toEqual(["a", "b", "c"])
    expect(ids(rest)).toEqual(["d", "e"])
  })
})
