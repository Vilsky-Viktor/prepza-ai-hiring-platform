import { describe, expect, it } from "vitest"

import { firstGrapheme, graphemes, sliceGraphemes } from "@/lib/graphemes"

describe("graphemes", () => {
  it("keeps a letter with its marks, an emoji and a Hindi cluster whole", () => {
    expect(graphemes("éa")).toEqual(["é", "a"])
    expect(graphemes("👩‍💻x")).toEqual(["👩‍💻", "x"])
    expect(graphemes("नमस्ते")).toEqual(["न", "म", "स्ते"])
  })

  it("takes the first one as an initial", () => {
    expect(firstGrapheme("👩‍💻 Ann")).toBe("👩‍💻")
    expect(firstGrapheme("Ölçü")).toBe("Ö")
    expect(firstGrapheme("")).toBe("")
  })

  it("slices by what people see", () => {
    expect(sliceGraphemes("नमस्ते", 2)).toBe("नम")
    expect(sliceGraphemes("e\u0301e\u0301", 1)).toBe("e\u0301")
    expect(sliceGraphemes("abc", 5)).toBe("abc")
  })
})
