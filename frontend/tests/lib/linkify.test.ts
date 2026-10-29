import { describe, expect, it } from "vitest"

import { linkParts } from "@/lib/linkify"

describe("linkParts", () => {
  it("keeps text without addresses as one plain part", () => {
    expect(linkParts("Call her on Monday")).toEqual([
      { text: "Call her on Monday" },
    ])
  })

  it("turns http and https addresses into links between plain text", () => {
    expect(
      linkParts("CV: https://example.com/cv?id=1 and http://a.org/x done")
    ).toEqual([
      { text: "CV: " },
      {
        text: "https://example.com/cv?id=1",
        url: "https://example.com/cv?id=1",
      },
      { text: " and " },
      { text: "http://a.org/x", url: "http://a.org/x" },
      { text: " done" },
    ])
  })

  it.each([".", ",", ")", "!", "?", ";", ":"])(
    "leaves a trailing %s out of the link",
    (mark) => {
      expect(linkParts(`See https://example.com/a${mark}`)).toEqual([
        { text: "See " },
        { text: "https://example.com/a", url: "https://example.com/a" },
        { text: mark },
      ])
    }
  )

  it("keeps a link inside brackets without the closing one", () => {
    expect(linkParts("(https://example.com/a).")).toEqual([
      { text: "(" },
      { text: "https://example.com/a", url: "https://example.com/a" },
      { text: ")." },
    ])
  })

  it.each([
    "javascript:alert(1)",
    "data:text/html,<b>x</b>",
    "ftp://example.com/file",
    "www.example.com",
  ])("leaves %s as text", (text) => {
    expect(linkParts(text).every((part) => !part.url)).toBe(true)
  })

  it("keeps a line break between two links as text", () => {
    expect(linkParts("https://a.com\nhttps://b.com")).toEqual([
      { text: "https://a.com", url: "https://a.com" },
      { text: "\n" },
      { text: "https://b.com", url: "https://b.com" },
    ])
  })

  it("returns no parts for an empty text", () => {
    expect(linkParts("")).toEqual([])
  })
})
